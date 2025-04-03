from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class EventPeriod(Base):
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('event.id'),nullable=False, index=True)
    started = Column(DateTime,nullable=True,index=True)
    ended = Column(DateTime,nullable=True, index=True)


    event = relationship('Event', back_populates='event_periods')