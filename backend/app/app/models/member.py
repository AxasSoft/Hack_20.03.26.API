from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Member(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime(),nullable=True,default=datetime.utcnow, index=True)
    delete_before_id = Column(Integer(), ForeignKey("message.id"),  nullable=True, index=True)
    user_id = Column(Integer(), ForeignKey("user.id", ondelete='CASCADE'),  nullable=False, index=True)

    delete_before = relationship('Message', foreign_keys=[delete_before_id])
    first_message_id = Column(Integer(), ForeignKey('message.id', ondelete='CASCADE'), nullable=True, index=True)
    last_message_id = Column(Integer(), ForeignKey("message.id", ondelete='CASCADE'),  nullable=True, index=True)

    ended = Column(DateTime(), nullable=True, index=True)
    started = Column(DateTime(), nullable=True, index=True)

    first_message = relationship('Message', foreign_keys=[first_message_id])
    last_message = relationship("Message", foreign_keys=[last_message_id])
    user = relationship('User', foreign_keys=[user_id], back_populates='member')
    initiated_chat = relationship("Chat", back_populates="initiator", foreign_keys="Chat.initiator_id", uselist=False)
    received_chat = relationship("Chat", back_populates="recipient", foreign_keys="Chat.recipient_id", uselist=False)

   

