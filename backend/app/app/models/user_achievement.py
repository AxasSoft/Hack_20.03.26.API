from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class UserAchievement(Base):
    id = Column(Integer, primary_key=True, index=True)

    achievement_id = Column(Integer, ForeignKey('achievement.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)

    achievement = relationship('Achievement', back_populates='user_achievements')
    user = relationship('User', back_populates='user_achievements')
