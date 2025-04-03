from datetime import datetime

from app.db.base_class import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship


class Adv(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    name = Column(String, nullable=True, default=None)
    cover = Column(String, nullable=True, default=None)
    link = Column(String, nullable=True, default=None)
    button_name = Column(String, nullable=True)

    slides = relationship('AdvSlide', back_populates='adv', lazy="joined", passive_deletes=True, cascade="all, delete-orphan")