from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AudioGideImage(Base):
    id = Column(Integer, primary_key=True, index=True)
    image = Column(String, nullable=True)

    audio_gide_id = Column(Integer, ForeignKey('audioguide.id', ondelete='CASCADE'), nullable=False, index=True)

    audio_guide = relationship('AudioGuide', back_populates='image')
