from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User
from app.schemas.user_report import Reason


class UserReport(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    subject_id = Column(Integer, ForeignKey(User.id), nullable=True, index=True)
    object_id = Column(Integer, ForeignKey(User.id), nullable=True, index=True)
    is_satisfy = Column(Boolean, nullable=True)
    reason = Column(Enum(Reason), nullable=True)
    additional_text = Column(String(), nullable=True)

    subject = relationship("User", foreign_keys=[subject_id], back_populates='subject_user_reports')
    object_ = relationship("User", foreign_keys=[object_id], back_populates='object_user_reports')
