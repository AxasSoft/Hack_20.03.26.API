from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class MessageExtraDatum(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey('message.id', ondelete='CASCADE'),nullable=False, index=True)
    read = Column(DateTime(), nullable=True)
    is_delete = Column(Boolean, nullable=False, default=False, index=True)

    user = relationship('User', backref=backref('extra_data', cascade='all, delete-orphan'))
    message = relationship('Message', back_populates='extra_data')
