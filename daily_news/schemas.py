from datetime import datetime
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = Field(default=True, description="Indicates whether the request succeeded")
    message: str = Field(..., description="Status or confirmation message")
    data: Optional[T] = Field(default=None, description="Payload returned by the operation")


class CategoryBase(BaseModel):
    """Base category schema with automatic whitespace trimming and validation."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique name of the news category")

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str) -> str:
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                raise ValueError("Category name cannot be empty or only whitespace")
            return trimmed
        return value


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(CategoryBase):
    """Schema for updating an existing category."""
    pass


class CategoryResponse(CategoryBase):
    """Schema representing a category returned from the database."""
    id: int = Field(..., description="Category ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    """Base schema for Post attributes."""
    title: str = Field(..., min_length=1, description="Title of the news article")
    description: Optional[str] = Field(default=None, description="Short summary or description")
    content: Optional[str] = Field(default=None, description="Full article text if available")
    image_url: Optional[str] = Field(default=None, description="URL of extracted article image or thumbnail")
    article_url: str = Field(..., min_length=1, description="Original URL of the article")
    source_name: Optional[str] = Field(default=None, description="Name of the news source or RSS feed")
    source_url: Optional[str] = Field(default=None, description="URL of the news source or feed website")
    guid: str = Field(..., min_length=1, description="Globally unique identifier from the feed")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    category_id: int = Field(..., gt=0, description="Foreign key reference to Category ID")

    @field_validator("title", "article_url", "guid", mode="before")
    @classmethod
    def trim_required_strings(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class PostCreate(PostBase):
    """Schema for creating a new post from RSS feed entries."""
    pass


class PostResponse(PostBase):
    """Schema representing a post returned from the database."""
    id: int = Field(..., description="Post ID")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record update timestamp")
    category: Optional[CategoryResponse] = Field(default=None, description="Associated Category details")

    model_config = ConfigDict(from_attributes=True)


class PaginatedPostResponse(BaseModel):
    """Paginated list of posts."""
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    total_records: int = Field(..., description="Total number of records")
    next_page: Optional[int] = Field(default=None, description="Next page number")
    previous_page: Optional[int] = Field(default=None, description="Previous page number")
    items: List[PostResponse] = Field(..., description="List of posts on current page")
