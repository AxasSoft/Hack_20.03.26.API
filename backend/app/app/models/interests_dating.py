from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


# модель для занкомств
class Interests(Base):
                     
    id = Column(Integer, primary_key=True, index=True)
    interest_name = Column(String)
    parent_interest_id = Column(Integer, ForeignKey("interests.id"))
    
    # Relationships
    subinterests = relationship("Interests", back_populates="parent_interest", remote_side=[id])
    parent_interest = relationship("Interests", back_populates="subinterests", remote_side=[parent_interest_id])
    profile_interests = relationship("ProfileInterests", back_populates="interest")