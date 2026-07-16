from pydantic import BaseModel, StringConstraints
from typing import List, Optional
from typing_extensions import Annotated

# Industry Standard: Define a reusable custom type for required strings
# This automatically strips whitespace and ensures the length is at least 1,
# utilizing Pydantic's underlying Rust core for maximum performance.
RequiredStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# --- Program ---
class ProgramBase(BaseModel):
    name: RequiredStr
    is_active: bool = True

class ProgramCreate(ProgramBase):
    pass

class ProgramOut(ProgramBase):
    id: int

    class Config:
        from_attributes = True

# --- Specialization ---
class SpecializationBase(BaseModel):
    name: RequiredStr
    is_active: bool = True
    program_id: int

class SpecializationCreate(SpecializationBase):
    pass

class SpecializationOut(SpecializationBase):
    id: int

    class Config:
        from_attributes = True

# --- Course ---
class CourseBase(BaseModel):
    name: RequiredStr
    code: RequiredStr
    is_active: bool = True
    specialization_id: int

class CourseCreate(CourseBase):
    pass

class CourseOut(CourseBase):
    id: int

    class Config:
        from_attributes = True

class TopicWithCompletionOut(BaseModel):
    id: int
    name: str
    is_completed: bool

class CourseDetailOut(CourseOut):
    subject: str
    progress: int
    status: str
    topics: List[TopicWithCompletionOut]

# --- Topic ---
class TopicBase(BaseModel):
    name: RequiredStr
    is_active: bool = True
    course_id: int

class TopicCreate(TopicBase):
    pass

class TopicOut(TopicBase):
    id: int

    class Config:
        from_attributes = True

# --- ProgressStatus ---
class ProgressStatusBase(BaseModel):
    name: str

class ProgressStatusCreate(ProgressStatusBase):
    pass

class ProgressStatusOut(ProgressStatusBase):
    id: int

    class Config:
        from_attributes = True

# --- CourseProgress ---
class CourseProgressBase(BaseModel):
    progress_status: int
    progress: int
    student_id: int
    course_id: int

class CourseProgressCreate(CourseProgressBase):
    pass

class CourseProgressOut(CourseProgressBase):
    id: int

    class Config:
        from_attributes = True

# --- IsComplete ---
class IsCompleteBase(BaseModel):
    status: bool = False
    student_id: int
    topic_id: int

class IsCompleteCreate(IsCompleteBase):
    pass

class IsCompleteOut(IsCompleteBase):
    id: int

    class Config:
        from_attributes = True
