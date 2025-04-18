from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime

from app.db.base_class import Base
from app.enums.excursion_booking_status import ExcursionBookingStatus


class ExcursionBooking(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    group_id = Column(Integer, ForeignKey('excursiongroup.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    status = Column(ENUM(ExcursionBookingStatus), nullable=False, default=ExcursionBookingStatus.NEW)
    excursion_id = Column(Integer,  ForeignKey('excursion.id'), nullable=False)
    comment = Column(String, nullable=True)


    excursion_group = relationship("ExcursionGroup", back_populates="bookings")
    excursion = relationship("Excursion", back_populates="bookings")
    user = relationship("User", back_populates="excursion_bookings")
    members = relationship("ExcursionMember", back_populates="booking", cascade="all, delete-orphan")

