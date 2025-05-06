import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, Date
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.transfer_type import TransferType


class Transfer(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    passengers_quantity = Column(Integer, nullable=False)
    type = Column(ENUM(TransferType), nullable=False)
    child_seat = Column(Boolean, nullable=True)
    animal = Column(Boolean, nullable=True)
    ski_supplies = Column(Boolean, nullable=True)
    comment = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("User", back_populates="transfers")