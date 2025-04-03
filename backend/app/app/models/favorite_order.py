from datetime import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FavoriteOrder(Base):
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey(
        'order.id', ondelete='CASCADE'), index=True)
    user_id = Column(Integer, ForeignKey(
        'user.id', ondelete='CASCADE'), index=True)

    order = relationship(
        'Order', back_populates='favorite_orders', lazy='joined')
    user = relationship(
        'User', back_populates='favorite_orders', lazy='joined')
