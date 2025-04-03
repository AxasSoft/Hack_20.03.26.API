from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Category(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    users = relationship('User', back_populates="category", lazy="dynamic")
    subcategories = relationship('Subcategory', cascade="all, delete-orphan", back_populates="category", lazy="dynamic")
