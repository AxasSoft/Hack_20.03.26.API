from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Member(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime(),nullable=False,default=datetime.utcnow, index=True)
    ended = Column(DateTime(), nullable=True, index=True)
    started = Column(DateTime(), nullable=True, index=True)
    chat_name = Column(String(), nullable=True, index=True)
    chat_cover = Column(String(), nullable=True, index=False)
    is_tech = Column(Boolean(), nullable=False, default=False, index=True)
    unread_count = Column(Integer(),nullable=False, index=False,default=0)
    user_id = Column(Integer(), ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    chat_id = Column(Integer(), ForeignKey('chat.id', ondelete='CASCADE'), nullable=False, index=True)
    first_message_id = Column(Integer(), ForeignKey('message.id', ondelete='CASCADE'), nullable=True, index=True)
    last_message_id = Column(Integer(), ForeignKey('message.id', ondelete='CASCADE'), nullable=True, index=True)

    user = relationship('User', backref=backref('members',cascade='all, delete-orphan'),lazy='joined')
    chat = relationship('Chat', back_populates='members',lazy='joined')
    first_message = relationship('Message', foreign_keys=[first_message_id])
    last_message = relationship('Message', foreign_keys=[last_message_id])
