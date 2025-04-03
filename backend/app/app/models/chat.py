from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from app.enums.type_chat import TypeChat

from app.db.base_class import Base


class Chat(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime(),nullable=False,default=datetime.utcnow, index=True)
    initiator_id = Column(Integer(), ForeignKey('member.id', ondelete='CASCADE'), nullable=True, index=True)
    recipient_id = Column(Integer(), ForeignKey('member.id', ondelete='CASCADE'), nullable=True, index=True)

    type_chat = Column(Enum(TypeChat), nullable=True)

    initiator = relationship("Member", back_populates="initiated_chat", foreign_keys=[initiator_id])
    recipient = relationship("Member", back_populates="received_chat", foreign_keys=[recipient_id])

