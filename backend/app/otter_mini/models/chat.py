from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Sequence
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Chat(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime(), nullable=False, default=datetime.utcnow, index=True)
    type_ = Column(String(), nullable=False, index=True)
    subtype = Column(String(), nullable=True, index=True)
    number = Column(Integer(), nullable=True, index=True)
    member_count = Column(Integer(), default=0)
    chat_name = Column(String, nullable=True, index=True)
    chat_cover = Column(String, nullable=True, index=True)
    initiator_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), index=True)
    recipient_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), index=True)

    members = relationship('Member', back_populates='chat', cascade='all, delete-orphan')

    initiator = relationship('User', foreign_keys=[initiator_id],
                             backref=backref('initiated_chats', cascade='all, delete-orphan'))
    recipient = relationship('User', foreign_keys=[recipient_id],
                             backref=backref('received_chats', cascade='all, delete-orphan'))
