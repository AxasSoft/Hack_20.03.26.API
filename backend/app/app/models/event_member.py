from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class AcceptingStatus(enum.Enum):
    wait = 0
    accepted = 1
    declined = 2

class EventMember(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'),nullable=False)
    event_id = Column(Integer, ForeignKey('event.id'),nullable=False)
    status = Column(Enum(AcceptingStatus), default=AcceptingStatus.wait, nullable=False)

    user = relationship('User', back_populates='event_members')
    event = relationship('Event', back_populates='event_members')