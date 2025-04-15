from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ExcursionCategoryImage(Base):
    id = Column(Integer, primary_key=True, index=True)

    image = Column(String, nullable=True)

    excursion_category_id = Column(Integer, ForeignKey('excursioncategory.id', ondelete='CASCADE'), nullable=False, index=True)

    excursion_category = relationship('ExcursionCategory', back_populates='background_image')
