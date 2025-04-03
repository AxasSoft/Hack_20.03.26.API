from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User


class Subscription(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    subject_id = Column(Integer, ForeignKey(User.id), nullable=True, index=True)
    object_id = Column(Integer, ForeignKey(User.id), nullable=True, index=True)

    subject = relationship("User", foreign_keys=[subject_id], back_populates='subject_subscriptions', lazy='joined')
    object_ = relationship("User", foreign_keys=[object_id], back_populates='object_subscriptions', lazy='joined')
