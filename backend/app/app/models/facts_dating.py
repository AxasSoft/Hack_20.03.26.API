from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base



class Facts(Base):
                     
    id = Column(Integer, primary_key=True, index=True)
    facts_name = Column(String)
    parent_facts_id = Column(Integer, ForeignKey("facts.id"))
    
    # Relationships
    parent_facts = relationship("Facts", back_populates="sub_facts", remote_side=[id])
    sub_facts = relationship("Facts", back_populates="parent_facts", remote_side=[parent_facts_id])
    profile_facts = relationship("ProfileFacts", back_populates="facts")