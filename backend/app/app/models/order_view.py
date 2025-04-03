from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.enums.mod_status import ModStatus


class OrderView(Base):
    id: int  = Column(Integer(), primary_key=True, index=True)
    order_id: int = Column(Integer(), ForeignKey('order.id', ondelete='CASCADE'), index=True)
    user_id: int = Column(Integer(), ForeignKey('user.id', ondelete='SET NULL'), index=True)
    created: datetime = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    is_viewed: bool = Column(Boolean(), default=True, server_default='True')

    order = relationship(
        'Order',
        back_populates='views_order',
        foreign_keys=[order_id],
        single_parent=True
    )

    user = relationship(
        'User',
        back_populates='views_order',
        foreign_keys=[user_id],
        passive_deletes=True
    )