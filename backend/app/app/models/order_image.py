from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class OrderImage(Base):
    id = Column(Integer, primary_key=True, index=True)

    image = Column(String, nullable=True)
    num = Column(Integer, nullable=True)

    order_id = Column(Integer, ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True)

    order = relationship('Order', back_populates='images')
