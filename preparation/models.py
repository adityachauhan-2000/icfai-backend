from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from config.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    logoColor = Column(String)
    accentColor = Column(String)
    textColor = Column(String, nullable=True)
    icon = Column(String) # e.g. "facebook", "google", "ey", "tcs" or an image URL/identifier

    rounds = relationship("InterviewRound", back_populates="company", cascade="all, delete-orphan", order_by="InterviewRound.order_index")

class InterviewRound(Base):
    __tablename__ = "interview_rounds"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)  # e.g., "Aptitude Assessment", "Interview"
    type = Column(String, nullable=False)   # e.g., "aptitude", "hr", "gd", "interview"
    timeLimit = Column(Integer, default=1800)  # Time in seconds
    description = Column(String, nullable=True)
    order_index = Column(Integer, default=0) # To order the rounds correctly
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="rounds")
    questions = relationship("AptitudeQuestion", back_populates="round", cascade="all, delete-orphan")

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, JSON

class AptitudeQuestion(Base):
    __tablename__ = "aptitude_questions"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("interview_rounds.id", ondelete="CASCADE"), nullable=False)
    q = Column(String, nullable=False)
    options = Column(JSON, nullable=False) # JSON array of strings
    answer = Column(Integer, nullable=False) # index of correct option
    shortcut = Column(String, nullable=True)
    category = Column(String, nullable=True)

    round = relationship("InterviewRound", back_populates="questions")

class InterviewResult(Base):
    __tablename__ = "interview_results"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    
    aptitude_score = Column(JSON, nullable=True)
    gd_analysis = Column(JSON, nullable=True)
    interview_analysis = Column(JSON, nullable=True)
    
    overall_score = Column(Integer, nullable=True)
    
    company = relationship("Company")
    # To avoid circular import, we can rely on standard relationship if Student is in metadata
    # student = relationship("Student")

class GDQuestion(Base):
    __tablename__ = "gd_questions"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("program.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)

    # To avoid circular dependency on Program model, we define foreign key directly and avoid relationship if needed,
    # or define it by string "Program".
    program = relationship("Program")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("program.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)

    program = relationship("Program")
