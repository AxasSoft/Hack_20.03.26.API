from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base

class ExcursionMember(Base):
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('excursionbooking.id'), nullable=False)
    excursion_group_id = Column(Integer, ForeignKey('excursiongroup.id'), nullable=False)
    full_name = Column(String, nullable=False)
    is_adult = Column(Boolean(), nullable=False)
    phone = Column(String, nullable=True)

    excursion_group = relationship("ExcursionGroup", back_populates="members")
    booking = relationship('ExcursionBooking', back_populates='members')

