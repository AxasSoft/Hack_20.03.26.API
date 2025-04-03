from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Message(Base):
    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer(), ForeignKey('message.id', ondelete='SET NULL'), nullable=True, index=True)

    created = Column(DateTime(), nullable=False, default=datetime.utcnow, index=True)
    text = Column(String(), nullable=True)
    is_read = Column(Boolean(), nullable=False, default=False, index=True, server_default='false')
    sender_id = Column(Integer(), ForeignKey('member.id', ondelete='SET NULL'), nullable=True, index=True)

    parent = relationship('Message', remote_side=[id], backref=backref('children'), lazy='joined')
    sender = relationship('Member', foreign_keys=[sender_id])
    attachments = relationship('Attachment', back_populates='message', cascade="all, delete-orphan")