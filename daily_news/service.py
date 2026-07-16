import re
import html
import math
import feedparser
from datetime import datetime, timezone
from time import mktime
from typing import Optional, Any, Dict, List, Tuple
from fastapi import status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from models import Category, Post, settings, logger, SessionLocal, Base, engine
from schemas import CategoryCreate, CategoryUpdate, PostCreate, PaginatedPostResponse


# =====================================================================
# Custom Exceptions (`exceptions/handlers.py`)
# =====================================================================

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """Exception raised when a resource conflict occurs (e.g., duplicates)."""
    def __init__(self, message: str = "Resource conflict occurred"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


# =====================================================================
# Helper Functions (`utils/helpers.py`)
# =====================================================================

def extract_image_url(entry: Dict[str, Any], raw_html: Optional[str] = None) -> Optional[str]:
    """Attempt to extract an image URL from RSS feed entry media attributes or HTML content."""
    # Check media_content
    if "media_content" in entry and isinstance(entry["media_content"], list):
        for media in entry["media_content"]:
            if isinstance(media, dict) and media.get("url"):
                return media["url"]

    # Check media_thumbnail
    if "media_thumbnail" in entry and isinstance(entry["media_thumbnail"], list):
        for thumb in entry["media_thumbnail"]:
            if isinstance(thumb, dict) and thumb.get("url"):
                return thumb["url"]

    # Check enclosures
    if "enclosures" in entry and isinstance(entry["enclosures"], list):
        for enclosure in entry["enclosures"]:
            if isinstance(enclosure, dict) and enclosure.get("type", "").startswith("image/") and enclosure.get("href"):
                return enclosure["href"]

    # Try extracting first <img> tag src from summary/content HTML
    if raw_html:
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def clean_html_text(text: Optional[str]) -> str:
    """Remove HTML tags, unescape HTML entities, and normalize whitespace."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_feed_timestamp(entry: Dict[str, Any]) -> datetime:
    """Extract and parse publication timestamp from RSS feed entry into UTC datetime."""
    time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if time_struct:
        try:
            dt = datetime.fromtimestamp(mktime(time_struct), timezone.utc)
            return dt
        except (ValueError, OverflowError, TypeError):
            pass
    return datetime.now(timezone.utc)


# =====================================================================
# Category Service (`services/category_service.py`)
# =====================================================================

class CategoryService:
    """Service for category CRUD and uniqueness checks."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Optional[Category]:
        """Fetch a category by name (case-insensitive)."""
        return self.db.query(Category).filter(
            func.lower(Category.name) == func.lower(name.strip())
        ).first()

    def create_category(self, category_data: CategoryCreate) -> Category:
        if self.get_by_name(category_data.name):
            raise ConflictException(f"Category '{category_data.name}' already exists")

        category = Category(name=category_data.name)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_all_categories(self) -> List[Category]:
        return self.db.query(Category).order_by(Category.id.asc()).all()

    def get_category(self, category_id: int) -> Category:
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise NotFoundException(f"Category ID {category_id} not found")
        return category

    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Category:
        category = self.get_category(category_id)
        existing = self.get_by_name(category_data.name)
        if existing and existing.id != category_id:
            raise ConflictException(f"Category '{category_data.name}' already exists")

        category.name = category_data.name
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self.get_category(category_id)
        self.db.delete(category)
        self.db.commit()


# =====================================================================
# Post Service (`services/post_service.py`)
# =====================================================================

class PostService:
    """Service for retrieving, searching, and paginating news posts."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_guid_or_url(self, guid: str, article_url: str) -> Optional[Post]:
        """Check if an article already exists by GUID or original URL."""
        return self.db.query(Post).filter(
            or_(Post.guid == guid, Post.article_url == article_url)
        ).first()

    def create_post(self, post_data: PostCreate) -> Post:
        """Create and persist a new news post."""
        post = Post(**post_data.model_dump())
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_posts(
        self,
        page: int = 1,
        limit: int = 10,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> PaginatedPostResponse:
        """Retrieve paginated posts filtered by category and search keywords."""
        query = self.db.query(Post).options(joinedload(Post.category))

        if category and category.strip():
            query = query.join(Category).filter(
                func.lower(Category.name) == func.lower(category.strip())
            )

        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Post.title.ilike(search_term),
                    Post.description.ilike(search_term),
                    Post.content.ilike(search_term)
                )
            )

        total_records = query.count()
        query = query.order_by(Post.published_at.desc().nullslast(), Post.created_at.desc())
        items = query.offset((page - 1) * limit).limit(limit).all()

        total_pages = math.ceil(total_records / limit) if limit > 0 and total_records > 0 else (1 if total_records == 0 else 0)
        if total_records == 0:
            total_pages = 0

        next_page = (page + 1) if page < total_pages else None
        previous_page = (page - 1) if 1 < page <= (total_pages + 1) else None

        return PaginatedPostResponse(
            current_page=page,
            total_pages=total_pages,
            total_records=total_records,
            next_page=next_page,
            previous_page=previous_page,
            items=items
        )

    def get_post(self, post_id: int) -> Post:
        """Fetch a specific post by ID or raise NotFoundException."""
        post = self.db.query(Post).options(joinedload(Post.category)).filter(Post.id == post_id).first()
        if not post:
            raise NotFoundException(f"Post ID {post_id} not found")
        return post


# =====================================================================
# Rss Service (`services/rss_service.py`)
# =====================================================================

class RssService:
    """Service handling synchronization of RSS feeds into the database."""

    def __init__(self, db: Session):
        self.db = db
        self.category_service = CategoryService(db)
        self.post_service = PostService(db)

    def _get_or_create_category(self, name: str) -> Category:
        category = self.category_service.get_by_name(name)
        if not category:
            logger.info(f"Creating new default category during RSS sync: {name}")
            category = self.category_service.create_category(CategoryCreate(name=name))
        return category

    def sync_feeds(self) -> Dict[str, int]:
        """Synchronize all configured RSS feeds, saving new articles and skipping duplicates."""
        feeds_mapping = settings.get_rss_feeds_mapping()

        stats = {
            "feeds_processed": 0,
            "articles_found": 0,
            "new_articles": 0,
            "duplicates": 0,
        }

        logger.info("Starting RSS feeds synchronization process...")

        for category_name, feed_url in feeds_mapping.items():
            if not feed_url or not feed_url.strip():
                continue

            stats["feeds_processed"] += 1
            logger.info(f"Processing RSS feed for category '{category_name}': {feed_url}")

            try:
                category = self._get_or_create_category(category_name)
                feed = feedparser.parse(feed_url)

                feed_title = feed.feed.get("title", category_name) if hasattr(feed, "feed") else category_name
                feed_link = feed.feed.get("link", feed_url) if hasattr(feed, "feed") else feed_url
                entries: List[Any] = feed.entries if hasattr(feed, "entries") else []

                for entry in entries:
                    stats["articles_found"] += 1

                    title = entry.get("title", "").strip() or "Untitled Article"
                    article_url = entry.get("link", "").strip()
                    guid = entry.get("id", entry.get("guid", article_url)).strip() or article_url

                    if not article_url or not guid:
                        continue

                    if self.post_service.get_by_guid_or_url(guid=guid, article_url=article_url):
                        stats["duplicates"] += 1
                        continue

                    raw_summary = entry.get("summary", entry.get("description", ""))
                    description = clean_html_text(raw_summary)
                    if len(description) > 500:
                        description = description[:497] + "..."

                    content = ""
                    if "content" in entry and isinstance(entry["content"], list) and len(entry["content"]) > 0:
                        content_obj = entry["content"][0]
                        if isinstance(content_obj, dict):
                            content = clean_html_text(content_obj.get("value", ""))
                    if not content:
                        content = clean_html_text(raw_summary)

                    image_url = extract_image_url(entry, raw_summary)
                    published_at = parse_feed_timestamp(entry)

                    post_data = PostCreate(
                        title=title,
                        description=description or None,
                        content=content or None,
                        image_url=image_url,
                        article_url=article_url,
                        source_name=feed_title,
                        source_url=feed_link,
                        guid=guid,
                        published_at=published_at,
                        category_id=category.id
                    )

                    try:
                        self.post_service.create_post(post_data)
                        stats["new_articles"] += 1
                    except Exception as e:
                        self.db.rollback()
                        logger.warning(f"Failed to save article '{title}': {str(e)}")

            except Exception as e:
                logger.error(f"Error while syncing RSS feed '{feed_url}': {str(e)}", exc_info=True)

        logger.info(f"RSS synchronization completed with stats: {stats}")
        return stats


# =====================================================================
# Database Seeder (`seed.py`)
# =====================================================================

DEFAULT_CATEGORIES = [
    "Finance",
    "Technology",
    "Startups",
    "Markets",
    "Economy",
]


def seed_default_categories() -> None:
    """Ensure default news categories exist in the database."""
    db = SessionLocal()
    try:
        service = CategoryService(db)
        for cat_name in DEFAULT_CATEGORIES:
            if not service.get_by_name(cat_name):
                service.create_category(CategoryCreate(name=cat_name))
                logger.info(f"Seeded default category: {cat_name}")
            else:
                logger.info(f"Category '{cat_name}' already exists.")
    except Exception as e:
        logger.error(f"Error seeding default categories: {str(e)}", exc_info=True)
    finally:
        db.close()


def run_seeder() -> None:
    """Standalone seeding execution if script is run directly."""
    from models import setup_logging
    setup_logging()
    logger.info("Starting database seeding process...")
    Base.metadata.create_all(bind=engine)
    seed_default_categories()
    logger.info("Database seeding finished.")


if __name__ == "__main__":
    run_seeder()
