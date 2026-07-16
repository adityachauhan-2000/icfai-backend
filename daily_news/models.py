import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Generator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy.sql import func


# =====================================================================
# Configuration Settings (`core/config.py`)
# =====================================================================

class Settings(BaseSettings):
    """Application configuration settings read from environment variables or .env file."""

    APP_NAME: str = "ICFAI Daily News Backend API"
    DATABASE_URL: str = "sqlite:///./news.db"
    API_VERSION: str = "/api/v1"

    # RSS Feeds
    TECHNOLOGY_RSS: str = "https://feeds.bbci.co.uk/news/technology/rss.xml"
    FINANCE_RSS: str = "https://feeds.bbci.co.uk/news/business/rss.xml"
    MARKETS_RSS: str = "https://www.investing.com/rss/news_301.rss"
    STARTUPS_RSS: str = "https://techcrunch.com/feed/"
    ECONOMY_RSS: str = "https://www.cnbc.com/id/10000664/device/rss/rss.html"

    # Scheduler Configuration
    SYNC_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_rss_feeds_mapping(self) -> Dict[str, str]:
        """Return a mapping of default category names to their respective RSS feed URLs."""
        return {
            "Technology": self.TECHNOLOGY_RSS,
            "Finance": self.FINANCE_RSS,
            "Markets": self.MARKETS_RSS,
            "Startups": self.STARTUPS_RSS,
            "Economy": self.ECONOMY_RSS,
        }


settings = Settings()


# =====================================================================
# Logging Setup (`core/logging.py`)
# =====================================================================

logger = logging.getLogger("icfai_news_api")


def setup_logging() -> None:
    """Configure application-wide logging formatters and handlers."""
    # Prevent adding duplicate handlers if already configured
    if logger.hasHandlers():
        return

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Also configure uvicorn and sqlalchemy loggers to align with application settings
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


# =====================================================================
# Database Setup (`core/database.py` & `dependencies.py`)
# =====================================================================

# For SQLite, check_same_thread must be False to allow multi-threading in FastAPI
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# ORM Models (`models/category.py` & `models/post.py`)
# =====================================================================

class Category(Base):
    """Category model representing news topic categories."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    posts = relationship("Post", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Post(Base):
    """Post model representing news articles collected from RSS feeds."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    article_url = Column(String, unique=True, index=True, nullable=False)
    source_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    guid = Column(String, unique=True, index=True, nullable=False)
    published_at = Column(DateTime(timezone=True), index=True, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    category = relationship("Category", back_populates="posts")

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title[:30]}...', guid='{self.guid}')>"
