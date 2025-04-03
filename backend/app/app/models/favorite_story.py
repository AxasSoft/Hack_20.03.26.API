import datetime

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FavoriteStory(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey('story.id'), nullable=False, index=True)

    user = relationship('User', back_populates='favorite_stories')
    story = relationship('Story', back_populates='favorite_stories')
