import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Story(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    text = Column(String, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    is_private = Column(Boolean, nullable=False, default=False, index=True)

    user = relationship(User, back_populates='stories', lazy='joined')
    attachments = relationship("StoryAttachment", cascade="all, delete-orphan", back_populates="story", lazy='joined', order_by="StoryAttachment.num")
    story_hashtags = relationship("StoryHashtag", cascade="all, delete-orphan", back_populates="story",lazy='joined')
    views = relationship("View", cascade="all, delete-orphan", back_populates="story", lazy='joined')
    hugs = relationship("Hug", cascade="all, delete-orphan", back_populates="story", lazy='joined')
    favorite_stories = relationship("FavoriteStory", cascade="all, delete-orphan", back_populates="story", lazy='joined')
    comments = relationship("Comment", cascade="all, delete-orphan", back_populates="story", lazy='dynamic')
    object_story_reports = relationship('StoryReport', cascade="all, delete-orphan", back_populates="object_",
                                       lazy="dynamic")
    story_hidings = relationship('StoryHiding', cascade="all, delete-orphan", back_populates="story", lazy="dynamic")
