import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# модель для юзера
class Interest(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


    user_interests = relationship("UserInterest", cascade="all, delete-orphan", back_populates="interest")
    event_interests = relationship("EventInterest", cascade="all, delete-orphan", back_populates="interest")