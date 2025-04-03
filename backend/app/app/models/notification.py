from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Notification(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime(), nullable=True, default=datetime.utcnow, index=True)
    title = Column(String(), nullable=True, index=True)
    body = Column(String(), nullable=True, index=True)
    user_id = Column(Integer(), ForeignKey('user.id', ondelete='CASCADE'), nullable=True, index=True)
    icon = Column(String(), nullable=True, index=True)

    order_id = Column(Integer(), ForeignKey('order.id', ondelete='CASCADE'), nullable=True, index=True)
    offer_id = Column(Integer(), ForeignKey('offer.id', ondelete='CASCADE'), nullable=True, index=True)
    stage = Column(Integer, nullable=True, index=True)

    is_read = Column(Boolean(), nullable=False, default=False, index=True)

    link = Column(String(), nullable=True)

    user = relationship('User', back_populates='notifications')
    order = relationship('Order')
    offer = relationship('Offer')


