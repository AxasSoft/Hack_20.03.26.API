from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Achievement(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime(), nullable=True, default=datetime.utcnow, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    cover = Column(String, nullable=True)
    counter = Column(Integer, nullable=False)
    reward = Column(Integer, nullable=False, server_default='0')

    user_achievements = relationship('UserAchievement', back_populates='achievement', passive_deletes=True)
