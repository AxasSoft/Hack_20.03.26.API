
from app.models import Event
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class EventInterest(Base):
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('event.id', ondelete='CASCADE'), nullable=False, index=True)
    interest_id = Column(Integer, ForeignKey('interest.id', ondelete='CASCADE'), nullable=False, index=True)

    event = relationship('Event', back_populates='event_interests')
    interest = relationship('Interest', back_populates='event_interests')