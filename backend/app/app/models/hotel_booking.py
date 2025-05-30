from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, Date, BigInteger
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.hotel_booking_status import HotelBookingStatus


class HotelBooking(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    hotel_name = Column(String, nullable=False)
    hotel_hid = Column(Integer, nullable=False, index=True)
    room_id = Column(Integer, nullable=True)
    room_name = Column(String, nullable=True)
    price = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    checkin = Column(Date, nullable=False)
    checkout = Column(Date, nullable=False)
    partner_order_id = Column(String, nullable=False)
    item_id = Column(Integer, nullable=False)
    order_id = Column(Integer, nullable=False)
    status = Column(ENUM(HotelBookingStatus), nullable=False, default=HotelBookingStatus.NEW)
    etg_pay_type = Column(String, nullable=False)
    is_need_credit_card_data = Column(Boolean, nullable=False, server_default='false')
    is_need_cvc = Column(Boolean, nullable=False, server_default='false')
    pay_uuid = Column(String, nullable=True)
    init_uuid = Column(String, nullable=True)
    has_free_cancellation = Column(Boolean, nullable=False, server_default='false')
    free_cancellation_before = Column(DateTime, nullable=True)
    rg_ext_hash = Column(BigInteger, nullable=False)


    user = relationship("User", back_populates="hotel_bookings")
    not_included_taxes = relationship("NotIncludedTax", back_populates="hotel_booking")

