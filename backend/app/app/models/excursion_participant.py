from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base

class ExcursionParticipant(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'),nullable=False)
    excursion_id = Column(Integer, ForeignKey('excursion.id'), nullable=False)
    excursion_group_id = Column(Integer, ForeignKey('excursiongroup.id'), nullable=True)


    user = relationship('User', back_populates='excursions_participant')
    excursion = relationship('Excursion', back_populates='participants')
    excursion_group = relationship("ExcursionGroup", back_populates="participants")

