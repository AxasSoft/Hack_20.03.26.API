from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class ExcursionCategory(Base):
    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    background_image = relationship("ExcursionCategoryImage", back_populates="excursion_category", cascade="all, delete-orphan")
    excursions = relationship("Excursion", back_populates="category", cascade="all, delete-orphan")

