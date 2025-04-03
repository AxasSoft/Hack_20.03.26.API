import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ServiceInfo(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.datetime.utcnow, index=True)
    updated = Column(DateTime, nullable=True, onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)
    slug = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    body = Column(String, nullable=True)
    link = Column(String, nullable=True)
    image = Column(String, nullable=True)
