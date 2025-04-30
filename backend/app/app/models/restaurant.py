from datetime import datetime
from email.policy import default
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.restaurant_type import RestaurantType


class Restaurant(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=False)
    two_gis_url = Column(String, nullable=True)
    loyalty_program = Column(Boolean, nullable=False, default=False)
    max_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    avg_check = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_reviews = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float, nullable=False, default=0.0)
    work_hours_weekdays = Column(String, nullable=True)
    work_hours_weekends = Column(String, nullable=True)
    delivery = Column(Boolean, nullable=False, default=False)
    type = Column(ENUM(RestaurantType), nullable=False)
    priority = Column(Integer, nullable=True)

    images = relationship("RestaurantImage", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("RestaurantReview", back_populates="restaurant", cascade="all, delete-orphan")
    phone_numbers = relationship("RestaurantPhoneNumber", back_populates="restaurant", cascade="all, delete-orphan")

