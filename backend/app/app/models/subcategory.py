from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Subcategory(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)

    category_id = Column(Integer,ForeignKey('category.id'), nullable=False)

    category = relationship('Category', back_populates="subcategories")

    orders = relationship('Order', cascade="all, delete-orphan", back_populates="subcategory", lazy="dynamic")

    promo_order = relationship('PromoOrder', back_populates='subcategory')