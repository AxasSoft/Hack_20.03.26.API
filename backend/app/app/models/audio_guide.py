from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base

class AudioGuide(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    audio_files = relationship("AudioGuideFile", back_populates="audio_guide")
    image = relationship("AudioGideImage", back_populates="audio_guide", uselist=False)

