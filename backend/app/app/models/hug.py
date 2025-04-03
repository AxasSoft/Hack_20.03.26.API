import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User, Story


class Hug(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey(Story.id), nullable=False, index=True)

    user = relationship(User, back_populates='hugs')
    story = relationship(Story, back_populates='hugs')
