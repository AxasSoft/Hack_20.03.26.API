from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User, Story


class StoryHiding(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=True, index=True)
    story_id = Column(Integer, ForeignKey(Story.id), nullable=True, index=True)

    user = relationship("User", back_populates='story_hidings')
    story = relationship("Story", back_populates='story_hidings')
