import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, Date
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class ExcursionReview(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    visit_date = Column(Date, nullable=False)
    description = Column(String, nullable=True)
    rating = Column(Float, nullable=False)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("User", back_populates="excursion_reviews")

    excursion_id = Column(Integer, ForeignKey('excursion.id'), nullable=False)
    excursion = relationship("Excursion", back_populates="reviews")
