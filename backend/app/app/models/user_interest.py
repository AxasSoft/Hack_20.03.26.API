from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class UserInterest(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    interest_id = Column(Integer, ForeignKey('interest.id', ondelete='CASCADE'), nullable=False, index=True)

    user = relationship('User', back_populates='user_interests')
    interest = relationship('Interest', back_populates='user_interests', lazy='joined')
