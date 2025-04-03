from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class DeletedMessage(Base):
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer(), ForeignKey('message.id'), nullable=False, index=True)
    member_id = Column(Integer(), ForeignKey('member.id'), nullable=False, index=True)

    message = relationship('Message')
    member = relationship('Member')

