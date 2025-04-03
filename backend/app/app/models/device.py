from datetime import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Device(Base):
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(INET(), nullable=True, index=True)
    x_real_ip = Column(INET(), nullable=True, index=True)
    user_agent = Column(String(), nullable=True, index=True)
    accept_language = Column(String(), nullable=True, index=True)
    created = Column(DateTime(), nullable=True, default=datetime.utcnow, index=True)
    detected_os = Column(String(), nullable=True, index=True)

    user_id = Column(Integer(), ForeignKey(User.id), nullable=False, index=True)

    user = relationship(User, back_populates='devices')
    firebase_tokens = relationship("FirebaseToken", cascade="all, delete-orphan", back_populates="device")
