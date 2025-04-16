from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.group_status import GroupStatus


class ExcursionGroup(Base):
    id = Column(Integer, primary_key=True, index=True)
    excursion_id = Column(Integer, ForeignKey('excursion.id'), nullable=False)
    started = Column(DateTime, nullable=False)
    ended = Column(DateTime, nullable=False)
    status = Column(ENUM(GroupStatus), nullable=False, default=GroupStatus.AVAILABLE)
    # max_group_size = Column(Integer, nullable=True)
    current_participants = Column(Integer, nullable=False, default=0)


    excursion = relationship("Excursion", back_populates="excursion_groups")
    participants = relationship("ExcursionParticipant", back_populates="excursion_group", cascade="all, delete-orphan")

