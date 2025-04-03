import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Info(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True, index=True)
    title = Column(String, nullable=True)
    body = Column(String, nullable=True)
    category = Column(Integer, nullable=False)
    image = Column(String, nullable=True)
    important = Column(Boolean, server_default='false')
    is_hidden = Column(Boolean, server_default='false', nullable=False)
    source = Column(String, nullable=True)
    user = relationship("User", back_populates="infos")

    promo_order = relationship('PromoOrder', back_populates='info')