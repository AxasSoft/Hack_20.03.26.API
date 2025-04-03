from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class ProfileAvatar(Base):
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=True)
    dating_profile_id = Column(Integer, ForeignKey('datingprofile.id', ondelete='CASCADE'))
    

    dating_profile = relationship("DatingProfile", back_populates="avatars")