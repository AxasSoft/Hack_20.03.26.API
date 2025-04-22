from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.group_status import GroupStatus


class ExcursionGroup(Base):
    id = Column(Integer, primary_key=True, index=True)
    excursion_id = Column(Integer, ForeignKey('excursion.id'), nullable=False)
    started = Column(DateTime, nullable=False)
    ended = Column(DateTime, nullable=True)
    status = Column(ENUM(GroupStatus), nullable=False, default=GroupStatus.AVAILABLE)
    current_members = Column(Integer, nullable=False, default=0)
    max_group_size = Column(Integer, nullable=True)

    excursion = relationship("Excursion", back_populates="excursion_groups")
    bookings = relationship("ExcursionBooking", back_populates="excursion_group", cascade="all, delete-orphan")
    members = relationship("ExcursionMember", back_populates="excursion_group", cascade="all, delete-orphan")

