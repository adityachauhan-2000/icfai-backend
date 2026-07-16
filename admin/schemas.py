from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentAdminBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    program_id: Optional[int] = None
    is_active: Optional[bool] = True

class StudentAdminCreate(StudentAdminBase):
    pass

class StudentAdminUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    program_id: Optional[int] = None
    is_active: Optional[bool] = None

class StudentAdminOut(StudentAdminBase):
    id: int
    branch: Optional[str] = None
    year: Optional[str] = None
    status: Optional[str] = "In Progress"
    studyPlanProgress: int = 0
    interviewsCompleted: int = 0
    averageMockScore: int = 0
    joinDate: str = "July 2026"
    
    class Config:
        from_attributes = True

class AdminStats(BaseModel):
    total_students: int
    active_students: int
    inactive_students: int
    last_month_active: int
    last_month_inactive: int
