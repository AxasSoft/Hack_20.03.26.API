from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.mod_status import ModStatus


class Event(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    # type_ = Column(String, nullable=False)
    started = Column(DateTime, nullable=True)
    ended = Column(DateTime, nullable=True)
    place = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    # period = Column(String, nullable=True)
    is_private = Column(Boolean, nullable=True)
    # price = Column(Integer, nullable=False,default=0)
    # start_link = Column(String, nullable=True)
    # report_link = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'),nullable=True)
    category_id = Column(Integer, ForeignKey('eventcategory.id'), nullable=True)
    max_event_members = Column(Integer, nullable=True)
    age = Column(Integer, nullable=False, server_default='0')
    link = Column(String, nullable=True)
    is_open = Column(Boolean, nullable=False, server_default="true", default=True)
    is_draft = Column(Boolean, nullable=False, server_default="false", default=False)
    price = Column(Integer, nullable=True)
    pay_link = Column(String, nullable=True)
    is_periodic = Column(Boolean, nullable=False,server_default="false", index=True, default=False)
    rating = Column(Float, nullable=True)
    status = Column(ENUM(ModStatus), nullable=False, server_default=ModStatus.created.name)
    moderation_comment = Column(String, nullable=True)

    user = relationship('User', back_populates='events')
    event_members = relationship("EventMember", back_populates="event", cascade="all, delete-orphan")
    category = relationship("EventCategory", back_populates="events")
    images = relationship("EventImage", back_populates="event", cascade="all, delete-orphan", order_by="EventImage.num")
    event_periods = relationship("EventPeriod", back_populates="event", cascade="all, delete-orphan", lazy='joined')
    event_interests = relationship("EventInterest", cascade="all, delete-orphan", back_populates="event")
    event_feedbacks = relationship("EventFeedback", cascade="all, delete-orphan", back_populates="event")