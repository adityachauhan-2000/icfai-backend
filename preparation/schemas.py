from pydantic import BaseModel
from typing import List, Optional

class InterviewRoundBase(BaseModel):
    label: str
    type: str
    description: Optional[str] = None
    timeLimit: Optional[int] = None
    order_index: int
    is_active: bool = True

class InterviewRoundCreate(InterviewRoundBase):
    pass

class InterviewRoundUpdate(BaseModel):
    label: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    timeLimit: Optional[int] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None

class InterviewRoundResponse(InterviewRoundBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True

class AptitudeQuestionBase(BaseModel):
    q: str
    options: List[str]
    answer: int
    shortcut: Optional[str] = None
    category: Optional[str] = None

class AptitudeQuestionResponse(AptitudeQuestionBase):
    id: int
    round_id: int

    class Config:
        from_attributes = True

class PaginatedAptitudeQuestionResponse(BaseModel):
    data: List[AptitudeQuestionResponse]
    total: int
    page: int
    limit: int
    
    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    name: str
    logoColor: Optional[str] = None
    accentColor: Optional[str] = None
    textColor: Optional[str] = None
    icon: str

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logoColor: Optional[str] = None
    accentColor: Optional[str] = None
    textColor: Optional[str] = None
    icon: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: int
    rounds: List[InterviewRoundResponse] = []

    class Config:
        from_attributes = True

class InterviewResultResponse(BaseModel):
    id: int
    company_id: int
    student_id: int
    aptitude_score: Optional[dict] = None
    gd_analysis: Optional[dict] = None
    interview_analysis: Optional[dict] = None
    overall_score: Optional[int] = None
    
    class Config:
        from_attributes = True

class GDQuestionResponse(BaseModel):
    id: int
    program_id: int
    question_text: str

    class Config:
        from_attributes = True

class InterviewQuestionResponse(BaseModel):
    id: int
    program_id: int
    question_text: str

    class Config:
        from_attributes = True
