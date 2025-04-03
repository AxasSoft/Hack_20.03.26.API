from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User, Story
from app.schemas.story_report import Reason


class StoryReport(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    subject_id = Column(Integer, ForeignKey(User.id), nullable=True, index=True)
    object_id = Column(Integer, ForeignKey(Story.id), nullable=True, index=True)
    is_satisfy = Column(Boolean, nullable=True, index=True)
    reason = Column(Enum(Reason), nullable=True, index=True)
    additional_text = Column(String(), nullable=True)

    subject = relationship("User", back_populates='subject_story_reports')
    object_ = relationship("Story", back_populates='object_story_reports')
