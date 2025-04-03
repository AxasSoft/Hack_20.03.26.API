import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User, Story


class StoryAttachment(Base):
    id = Column(Integer, primary_key=True, index=True)
    main_link = Column(String, nullable=False)
    cover_link = Column(String, nullable=True)
    is_image = Column(Boolean, nullable=False, default=False, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey(Story.id), nullable=True, index=True)
    num = Column(Integer, nullable=True)

    user = relationship(User, back_populates='stories_attachments')
    story = relationship(Story, back_populates='attachments')
