from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class ProfileLike(Base):
    
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)

    liker_dating_profile_id = Column(Integer, ForeignKey("datingprofile.id",  ondelete='CASCADE'))  # Профиль, который ставит лайк
    liked_dating_profile_id = Column(Integer, ForeignKey("datingprofile.id",  ondelete='CASCADE'))  # Профиль, который получает лайк

    like = Column(Boolean(), nullable=True)

    mutual = Column(Boolean, default=False, server_default='false')

    liker_estimate_type = Column(Integer(), nullable=True) # Число для весов

    # релы 
    liker_profile = relationship("DatingProfile", foreign_keys=[liker_dating_profile_id])
    liked_profile = relationship("DatingProfile", foreign_keys=[liked_dating_profile_id])