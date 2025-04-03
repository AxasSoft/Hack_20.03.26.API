from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class EventCategory(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)

    events = relationship("Event", back_populates="category")

