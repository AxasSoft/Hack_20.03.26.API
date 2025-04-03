from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base



class GenreMusic(Base):
                     
    id = Column(Integer, primary_key=True, index=True)
    genre_music_name = Column(String)
    parent_genre_music_id = Column(Integer, ForeignKey("genremusic.id"))
    
    # Relationships
    parent_genre_music = relationship("GenreMusic", back_populates="sub_genre_music", remote_side=[id])
    sub_genre_music = relationship("GenreMusic", back_populates="parent_genre_music", remote_side=[parent_genre_music_id])
    profile_genre_music = relationship("ProfileGenreMusic", back_populates="genre_music")
