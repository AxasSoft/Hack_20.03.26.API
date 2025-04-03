
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, FLOAT
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class RatingWeights(Base):
    id = Column(Integer(), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("datingprofile.id", ondelete='CASCADE')) # Идентификатор пользователя, для которого вычисляется релевантность.
    profile_id = Column(Integer(), ForeignKey("datingprofile.id", ondelete='CASCADE')) # Идентификатор пользователя, для которого вычисляется релевантность.
    interest_weight = Column(FLOAT(), nullable=True)
    genre_music_weight = Column(FLOAT(), nullable=True)
    facts_weight = Column(FLOAT(), nullable=True)
    education_weight = Column(FLOAT(), nullable=True)
    work_weight = Column(FLOAT(), nullable=True)
    films_weight = Column(FLOAT(), nullable=True)
    book_weight = Column(FLOAT(), nullable=True)
    about_weight = Column(FLOAT(), nullable=True)

    total_weights = Column(FLOAT(), nullable=True)


    # релы 
    user = relationship("DatingProfile", back_populates='rating_user', foreign_keys=[user_id])
    profile = relationship("DatingProfile", back_populates='rating_profile', foreign_keys=[profile_id])