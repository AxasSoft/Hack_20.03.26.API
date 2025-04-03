from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Message(Base):
    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer(), ForeignKey('message.id', ondelete='SET NULL'), nullable=True, index=True)

    sender_id = Column(Integer(), ForeignKey('member.id', ondelete='CASCADE'), index=True)
    user_id = Column(Integer(), ForeignKey('user.id'), index=True)

    parent_type = Column(String, nullable=True)
    created = Column(DateTime(), nullable=False, default=datetime.utcnow, index=True)
    body = Column(String(), nullable=True)
    is_event = Column(String(), nullable=False, default=False, index=True)
    is_delete = Column(Boolean(), nullable=False, server_default='false', index=True)

    parent = relationship('Message', remote_side=[id], backref=backref('children'), lazy='joined')
    sender = relationship('Member', foreign_keys=[sender_id], lazy='joined')
    user = relationship('User', backref=backref('messages', cascade='all, delete-orphan'))

    attachments = relationship('Attachment', back_populates='message', cascade='all, delete-orphan', lazy='joined')
    extra_data = relationship('MessageExtraDatum', back_populates='message', cascade='all, delete-orphan', lazy='joined')
