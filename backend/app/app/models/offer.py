import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Offer(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    text = Column(String, nullable=True)
    is_winner = Column(Boolean, nullable=True, default=None)
    order_id = Column(Integer, ForeignKey('order.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    type = Column(String, nullable=True)
    address = Column(String, nullable=True)

    order = relationship('Order', back_populates='offers')
    user = relationship('User', back_populates='offers')

    feedbacks = relationship('Feedback', cascade="all, delete-orphan", back_populates="offer", lazy="dynamic")
