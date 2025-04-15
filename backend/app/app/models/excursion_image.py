from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ExcursionImage(Base):
    id = Column(Integer, primary_key=True, index=True)

    image = Column(String, nullable=True)
    num = Column(Integer, nullable=True)

    excursion_id = Column(Integer, ForeignKey('excursion.id', ondelete='CASCADE'), nullable=False, index=True)

    excursion = relationship('Excursion', back_populates='images')
