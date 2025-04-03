from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Hashtag(Base):
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False, unique=True, index=True)

    hashtag_stories = relationship(
        "StoryHashtag",
        cascade="all, delete-orphan",
        back_populates="hashtag",
        lazy='dynamic'
    )
