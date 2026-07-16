from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base



class Program(Base):
    __tablename__ = "program"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)

    specializations = relationship("Specialization", back_populates="program")
    students = relationship("Student", back_populates="program")

class Specialization(Base):
    __tablename__ = "specialization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    program_id = Column(Integer, ForeignKey("program.id"))

    program = relationship("Program", back_populates="specializations")
    courses = relationship("Course", back_populates="specialization")

class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    specialization_id = Column(Integer, ForeignKey("specialization.id"))

    specialization = relationship("Specialization", back_populates="courses")
    topics = relationship("Topic", back_populates="course")
    course_progresses = relationship("CourseProgress", back_populates="course")

class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    course_id = Column(Integer, ForeignKey("course.id"))
    is_active = Column(Boolean, default=True)

    course = relationship("Course", back_populates="topics")
    completions = relationship("IsComplete", back_populates="topic")

class ProgressStatus(Base):
    __tablename__ = "progress_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # e.g., in progress, complete, upcoming

    course_progresses = relationship("CourseProgress", back_populates="status_ref")

class CourseProgress(Base):
    __tablename__ = "course_progress"

    id = Column(Integer, primary_key=True, index=True)
    progress_status = Column(Integer, ForeignKey("progress_status.id"))
    progress = Column(Integer)
    student_id = Column(Integer, ForeignKey("student.id"))
    course_id = Column(Integer, ForeignKey("course.id"))

    status_ref = relationship("ProgressStatus", back_populates="course_progresses")
    student = relationship("Student", back_populates="course_progresses")
    course = relationship("Course", back_populates="course_progresses")

class IsComplete(Base):
    __tablename__ = "is_complete"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(Boolean, default=False)
    student_id = Column(Integer, ForeignKey("student.id"))
    topic_id = Column(Integer, ForeignKey("topic.id"))

    student = relationship("Student", back_populates="topic_completions")
    topic = relationship("Topic", back_populates="completions")
