
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base




class ProfileInterests(Base):

    dating_profile_id = Column(Integer, ForeignKey("datingprofile.id",  ondelete='CASCADE'), primary_key=True)
    interest_id = Column(Integer, ForeignKey("interests.id", ondelete='CASCADE'), primary_key=True)
    
    # Relationships
    dating_profile = relationship("DatingProfile", back_populates="profile_interests")
    interest = relationship("Interests", back_populates="profile_interests")
