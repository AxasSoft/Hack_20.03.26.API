import datetime

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FeedbackOrder(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated = Column(DateTime(), nullable=True)

    title = Column(String(), nullable=True)
    text = Column(String(), nullable=True)
    rate = Column(Integer, nullable=True)

    creator_id = Column(Integer(), ForeignKey('user.id'), nullable=True)

    order_id = Column(Integer(), ForeignKey('order.id'), nullable=True)
    owner_order_id = Column(Integer(), ForeignKey('user.id'), nullable=True)

    order = relationship(
        'Order',
        back_populates='feedback_order',
    )

    creator = relationship(
        'User',
        back_populates='creator_feedback',
        foreign_keys=[creator_id]
    )

    owner_order = relationship(
        'User',
        back_populates='owner_order_feedback',
        foreign_keys=[owner_order_id]
    )