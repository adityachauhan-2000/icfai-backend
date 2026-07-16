from pydantic import BaseModel, StringConstraints, model_validator, computed_field
from typing import List, Optional, Any
from typing_extensions import Annotated
from datetime import datetime
import re

# Industry Standard: Define a reusable custom type for required strings
RequiredStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CaseStudyBase(BaseModel):
    name: RequiredStr
    subtitle: RequiredStr
    thumbnail: Optional[str] = None
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    author: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class CaseStudyCreate(CaseStudyBase):
    pass


class CaseStudyUpdate(BaseModel):
    name: Optional[RequiredStr] = None
    subtitle: Optional[RequiredStr] = None
    thumbnail: Optional[str] = None
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    author: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CaseStudyResourceCreate(BaseModel):
    video_title: Optional[RequiredStr] = None
    youtube_url: Optional[RequiredStr] = None
    youtube_video_id: Optional[RequiredStr] = None
    description: Optional[str] = None
    display_order: int = 1
    is_important: bool = False
    is_active: bool = True

    @model_validator(mode="before")
    @classmethod
    def process_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        # Map title <-> video_title
        if "title" in values and not values.get("video_title"):
            values["video_title"] = values["title"]
        elif "video_title" in values and not values.get("title"):
            values["title"] = values["video_title"]

        # Map url <-> youtube_url
        if "url" in values and not values.get("youtube_url"):
            values["youtube_url"] = values["url"]
        elif "youtube_url" in values and not values.get("url"):
            values["url"] = values["youtube_url"]

        # Extract youtube_video_id if missing
        url = values.get("youtube_url") or values.get("url")
        vid_id = values.get("youtube_video_id")
        if url and (not vid_id or not str(vid_id).strip()):
            match = re.search(r"^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*", str(url))
            if match and len(match.group(2)) == 11:
                values["youtube_video_id"] = match.group(2)
            else:
                values["youtube_video_id"] = "dQw4w9WgXcQ"
        return values


class CaseStudyResourceUpdate(BaseModel):
    video_title: Optional[RequiredStr] = None
    youtube_url: Optional[RequiredStr] = None
    youtube_video_id: Optional[RequiredStr] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_important: Optional[bool] = None
    is_active: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def process_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        if "title" in values and not values.get("video_title"):
            values["video_title"] = values["title"]
        if "url" in values and not values.get("youtube_url"):
            values["youtube_url"] = values["url"]
        return values


class CaseStudyResourceOut(BaseModel):
    id: int
    case_study_id: int
    video_title: str
    youtube_url: str
    youtube_video_id: str
    description: Optional[str] = None
    display_order: int = 1
    is_important: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def title(self) -> str:
        return self.video_title

    @computed_field
    @property
    def url(self) -> str:
        return self.youtube_url

    class Config:
        from_attributes = True


class CaseStudyResourceBatchInput(BaseModel):
    resources: List[CaseStudyResourceCreate]


class CaseStudyResourceListResponse(BaseModel):
    resources: List[CaseStudyResourceOut]


class CaseStudyOut(CaseStudyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resources: Optional[List[CaseStudyResourceOut]] = None

    class Config:
        from_attributes = True


class CaseStudyListResponse(BaseModel):
    case_studies: List[CaseStudyOut]

