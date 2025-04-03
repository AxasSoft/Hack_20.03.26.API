from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AdvSlide(Base):
    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=True)
    body = Column(String, nullable=True)
    img = Column(String, nullable=True)

    adv_id = Column(Integer, ForeignKey('adv.id', ondelete='CASCADE'), nullable=False, index=True)

    adv = relationship('Adv', back_populates='slides')