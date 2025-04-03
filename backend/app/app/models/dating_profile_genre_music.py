from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base




class ProfileGenreMusic(Base):

    dating_profile_id = Column(Integer, ForeignKey("datingprofile.id",  ondelete='CASCADE'), primary_key=True)
    sub_genre_music_id = Column(Integer, ForeignKey("genremusic.id",  ondelete='CASCADE'), primary_key=True)

    # Relationships
    dating_profile = relationship("DatingProfile", back_populates="profile_genre_music")
    genre_music  = relationship("GenreMusic", back_populates="profile_genre_music")
