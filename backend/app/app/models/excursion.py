from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.excursion_status import ExcursionStatus


class Excursion(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    tips = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    max_height = Column(Float, nullable=True)
    min_height = Column(Float, nullable=True)
    route_length = Column(Float, nullable=True)
    max_group_size = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_reviews = Column(Integer, nullable=True)
    avg_rating = Column(Float, nullable=True)
    priority = Column(Integer, nullable=True)
    excursion_status = Column(ENUM(ExcursionStatus), nullable=False, default=ExcursionStatus.OPEN)
    category_id = Column(Integer, ForeignKey('excursioncategory.id'), nullable=False)

    category = relationship("ExcursionCategory", back_populates="excursions")
    images = relationship("ExcursionImage", back_populates="excursion", cascade="all, delete-orphan", order_by="ExcursionImage.num")
    bookings = relationship("ExcursionBooking", back_populates="excursion", cascade="all, delete-orphan")
    excursion_groups = relationship("ExcursionGroup", back_populates="excursion", cascade="all, delete-orphan")
    reviews = relationship("ExcursionReview", back_populates="excursion")

