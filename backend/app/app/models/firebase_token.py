from datetime import datetime
from typing import TYPE_CHECKING

from app.models import User, Device
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FirebaseToken(Base):
    id = Column(Integer, primary_key=True, index=True)
    value = Column(String(),nullable=False)
    created = Column(DateTime(), nullable=True, default=datetime.utcnow, index=True)

    device_id = Column(Integer(), ForeignKey(Device.id), nullable=False, index=True)

    device = relationship(Device, back_populates='firebase_tokens')
