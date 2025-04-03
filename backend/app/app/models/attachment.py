from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Attachment(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime(), nullable=False, default=datetime.utcnow, index=True)
    link = Column(String(), nullable=False)
    note = Column(String(), nullable=True)
    message_id = Column(Integer(), ForeignKey('message.id'), nullable=True, index=True)

    message = relationship('Message', back_populates='attachments')