from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, Query, status, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler

from models import get_db, settings, logger, setup_logging, Base, engine, SessionLocal
from schemas import CategoryCreate, CategoryUpdate, CategoryResponse, PostResponse, PaginatedPostResponse, APIResponse
from service import CategoryService, PostService, RssService, AppException, NotFoundException, ConflictException, seed_default_categories


# =====================================================================
# API Routers (`routers/router.py`)
# =====================================================================

category_router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Category Not Found"},
        409: {"description": "Conflict - Category already exists"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)

post_router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Post Not Found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)

rss_router = APIRouter(
    prefix="/rss",
    tags=["RSS Synchronization"],
    responses={
        500: {"description": "Internal Server Error"}
    }
)


@category_router.post(
    "",
    response_model=APIResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new news category",
    description="Registers a new news topic category. Category names must be unique and non-empty."
)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db)
) -> APIResponse[CategoryResponse]:
    service = CategoryService(db)
    category = service.create_category(category_data)
    return APIResponse(
        success=True,
        message="Category created successfully",
        data=CategoryResponse.model_validate(category)
    )


@category_router.get(
    "",
    response_model=APIResponse[List[CategoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all categories",
    description="Fetches a list of all available news categories ordered by ID."
)
def get_categories(
    db: Session = Depends(get_db)
) -> APIResponse[List[CategoryResponse]]:
    service = CategoryService(db)
    categories = service.get_all_categories()
    return APIResponse(
        success=True,
        message="Categories retrieved successfully",
        data=[CategoryResponse.model_validate(c) for c in categories]
    )


@category_router.get(
    "/{id}",
    response_model=APIResponse[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get category by ID",
    description="Retrieves specific details of a news category by its ID."
)
def get_category_by_id(
    id: int,
    db: Session = Depends(get_db)
) -> APIResponse[CategoryResponse]:
    service = CategoryService(db)
    category = service.get_category(id)
    return APIResponse(
        success=True,
        message="Category fetched successfully",
        data=CategoryResponse.model_validate(category)
    )


@category_router.put(
    "/{id}",
    response_model=APIResponse[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Update category details",
    description="Updates the name of an existing news category by its ID."
)
def update_category(
    id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db)
) -> APIResponse[CategoryResponse]:
    service = CategoryService(db)
    category = service.update_category(id, category_data)
    return APIResponse(
        success=True,
        message="Category updated successfully",
        data=CategoryResponse.model_validate(category)
    )


@category_router.delete(
    "/{id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a category",
    description="Deletes a news category by its ID along with any associated posts if cascaded."
)
def delete_category(
    id: int,
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    service = CategoryService(db)
    service.delete_category(id)
    return APIResponse(
        success=True,
        message="Category deleted successfully",
        data=None
    )


@post_router.get(
    "",
    response_model=APIResponse[PaginatedPostResponse],
    status_code=status.HTTP_200_OK,
    summary="List and filter news posts",
    description="Retrieves a paginated list of news articles sorted newest first, with optional keyword search across title/description/content and optional filtering by category name."
)
def get_posts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of posts per page (max 100)"),
    category: Optional[str] = Query(None, description="Filter posts by exact or partial category name (case-insensitive)"),
    search: Optional[str] = Query(None, description="Keyword search inside title, description, and article content"),
    db: Session = Depends(get_db)
) -> APIResponse[PaginatedPostResponse]:
    service = PostService(db)
    paginated_result = service.get_posts(page=page, limit=limit, category=category, search=search)
    return APIResponse(
        success=True,
        message="Posts retrieved successfully",
        data=paginated_result
    )


@post_router.get(
    "/{id}",
    response_model=APIResponse[PostResponse],
    status_code=status.HTTP_200_OK,
    summary="Get post by ID",
    description="Retrieves full details of a specific news article by its unique ID."
)
def get_post_by_id(
    id: int,
    db: Session = Depends(get_db)
) -> APIResponse[PostResponse]:
    service = PostService(db)
    post = service.get_post(id)
    return APIResponse(
        success=True,
        message="Post fetched successfully",
        data=PostResponse.model_validate(post)
    )


@rss_router.post(
    "/sync",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Synchronize news articles from RSS feeds",
    description="Triggers an immediate synchronization of all configured RSS feeds into the database, skipping duplicates."
)
def sync_rss_feeds(
    db: Session = Depends(get_db)
) -> APIResponse[Dict[str, Any]]:
    service = RssService(db)
    sync_data = service.sync_feeds()
    return APIResponse(
        success=True,
        message="RSS synchronization completed",
        data=sync_data
    )


router = APIRouter()
router.include_router(category_router)
router.include_router(post_router)
router.include_router(rss_router)


# =====================================================================
# Exception Handlers (`exceptions/handlers.py`)
# =====================================================================

def register_exception_handlers(app_instance: FastAPI) -> None:
    """Register custom exception handlers with the FastAPI application instance."""

    @app_instance.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "errors": []
            }
        )

    @app_instance.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for error in exc.errors():
            field_name = " -> ".join(str(loc) for loc in error.get("loc", []))
            errors.append({
                "field": field_name,
                "msg": error.get("msg", "Invalid value"),
                "type": error.get("type", "")
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Request validation failed",
                "errors": errors
            }
        )

    @app_instance.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error(f"Database failure encountered: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An internal database error occurred",
                "errors": []
            }
        )

    @app_instance.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception encountered: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected internal server error occurred",
                "errors": []
            }
        )


# =====================================================================
# Background Scheduler & Lifespan (`main.py`)
# =====================================================================

scheduler = BackgroundScheduler()


def scheduled_rss_sync_job() -> None:
    """Background task executed periodically by APScheduler to sync RSS feeds."""
    logger.info("Executing scheduled periodic RSS synchronization task...")
    db = SessionLocal()
    try:
        service = RssService(db)
        service.sync_feeds()
    except Exception as e:
        logger.error(f"Error during background RSS sync: {str(e)}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown events."""
    # Startup sequence
    setup_logging()
    logger.info("Startup sequence initiated for ICFAI Daily News Backend API.")

    # Ensure database schema is created if not already managed by migrations
    Base.metadata.create_all(bind=engine)

    # Automatically seed default categories without creating duplicates
    seed_default_categories()

    # Configure and start background RSS synchronization scheduler
    scheduler.add_job(
        scheduled_rss_sync_job,
        trigger="interval",
        minutes=settings.SYNC_INTERVAL_MINUTES,
        id="rss_sync_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"APScheduler started: RSS sync job configured every {settings.SYNC_INTERVAL_MINUTES} minutes.")

    yield

    # Shutdown sequence
    logger.info("Shutdown sequence initiated for ICFAI Daily News Backend API.")
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down successfully.")
    logger.info("Application shutdown completed cleanly.")


# =====================================================================
# FastAPI Application Setup (`main.py`)
# =====================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION.strip("/"),
    description="Production-ready REST API backend for Daily News application powered by FastAPI, SQLAlchemy 2.x, SQLite, and APScheduler.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom global exception handlers
register_exception_handlers(app)

# Include API routers under the version prefix
app.include_router(router, prefix=settings.API_VERSION)


@app.get(
    f"{settings.API_VERSION}/health",
    tags=["Health"],
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Checks service status, database connectivity, and returns general system health."
)
def health_check() -> Dict[str, Any]:
    """Health status verification endpoint."""
    return {
        "success": True,
        "message": "Service is healthy and operational",
        "data": {
            "service": settings.APP_NAME,
            "version": settings.API_VERSION,
            "status": "ok"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("router:app", host="0.0.0.0", port=8000, reload=True)
