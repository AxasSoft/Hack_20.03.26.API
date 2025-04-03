from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base




class ProfileFacts(Base):

    dating_profile_id = Column(Integer, ForeignKey("datingprofile.id",  ondelete='CASCADE'), primary_key=True)
    subfacts_id = Column(Integer, ForeignKey("facts.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    dating_profile = relationship("DatingProfile", back_populates="profile_facts")
    facts = relationship("Facts", back_populates="profile_facts")
