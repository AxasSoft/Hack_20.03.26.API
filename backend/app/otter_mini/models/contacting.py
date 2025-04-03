from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Contacting(Base):
    id = Column(Integer(), primary_key=True, index=True)
    created = Column(DateTime(),nullable=False,default=datetime.utcnow, index=True)
    body = Column(String(), nullable=True)
    back_contacts = Column(String(), nullable=True)
    user_id = Column(Integer(), ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True, index=True)
    processed = Column(DateTime(), nullable=True, index=True)

    user = relationship('User', backref=backref('contactings',cascade='all, delete-orphan'), lazy='joined')

