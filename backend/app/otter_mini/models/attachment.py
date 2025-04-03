from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Attachment(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime(), nullable=False, index=True,default=datetime.utcnow)
    link = Column(String(), nullable=False)
    type = Column(String(), nullable=False, index=True)
    user_id = Column(Integer(), ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), index=True, nullable=False)
    message_id = Column(Integer(), ForeignKey('message.id', ondelete='CASCADE'), nullable=True, index=True)

    user = relationship('User', backref=backref('attachments',cascade='all, delete-orphan'),lazy='joined')
    message = relationship('Message', back_populates='attachments')