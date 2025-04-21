from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class RestaurantPhoneNumber(Base):
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=True)
    restaurant_id = Column(Integer, ForeignKey('restaurant.id', ondelete='CASCADE'), nullable=False, index=True)

    restaurant = relationship('Restaurant', back_populates='phone_numbers')
