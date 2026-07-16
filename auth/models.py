from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    program_id = Column(Integer, ForeignKey("program.id"))
    is_active = Column(Boolean, default=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)  # Using String for phone numbers to handle '+' or formatting
    hash_pass = Column(String)  # Using String for password hashes
    profile_image = Column(String, nullable=True)
    
    # Relationships
    program = relationship("Program", back_populates="students")
    course_progresses = relationship("CourseProgress", back_populates="student")
    topic_completions = relationship("IsComplete", back_populates="student")

class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hash_pass = Column(String)
    profile_image = Column(String, nullable=True)
