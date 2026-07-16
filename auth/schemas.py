from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    program_id: Optional[int] = None

class StudentLogin(BaseModel):
    email: EmailStr
    password: str

class StudentOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    program_id: Optional[int] = None
    is_active: bool
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class StudentUpdate(BaseModel):
    name: str

class StudentPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class AdminBase(BaseModel):
    name: str
    email: str

class AdminCreate(AdminBase):
    password: str

class AdminLogin(BaseModel):
    email: str
    password: str

class AdminResponse(AdminBase):
    id: int
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True

class AdminUpdate(BaseModel):
    name: str

class AdminPasswordUpdate(BaseModel):
    current_password: str
    new_password: str
