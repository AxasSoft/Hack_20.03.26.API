from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AudioGuideFile(Base):
    id = Column(Integer, primary_key=True, index=True)
    audio = Column(String, nullable=False)

    audio_guide_id = Column(Integer, ForeignKey('audioguide.id', ondelete='CASCADE'), nullable=False, index=True)

    audio_guide = relationship('AudioGuide', back_populates='audio_file')
