from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, Date, BigInteger
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.hotel_booking_status import HotelBookingStatus


class NotIncludedTax(Base):
    id = Column(Integer, primary_key=True, index=True)
    hotel_booking_id = Column(Integer, ForeignKey('hotelbooking.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)


    hotel_booking = relationship("HotelBooking", back_populates="not_included_taxes")

