from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class CaseStudy(Base):
    __tablename__ = "case_study"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    subtitle = Column(String)
    thumbnail = Column(String)
    youtube_video_id = Column(String, index=True)
    youtube_url = Column(String)
    author = Column(String)
    display_order = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    resources = relationship("CaseStudyResource", back_populates="case_study", cascade="all, delete-orphan", order_by="CaseStudyResource.display_order.asc()")


class CaseStudyResource(Base):
    __tablename__ = "case_study_resource"

    id = Column(Integer, primary_key=True, index=True)
    case_study_id = Column(Integer, ForeignKey("case_study.id", ondelete="CASCADE"), nullable=False, index=True)
    video_title = Column(String, nullable=False)
    youtube_url = Column(String, nullable=False)
    youtube_video_id = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    display_order = Column(Integer, default=1, index=True)
    is_important = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    case_study = relationship("CaseStudy", back_populates="resources")

