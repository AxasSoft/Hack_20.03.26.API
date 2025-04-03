import datetime

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Feedback(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    text = Column(String, nullable=True)
    rate = Column(Integer, nullable=True)
    is_offer = Column(Boolean, nullable=False)
    offer_id = Column(Integer, ForeignKey('offer.id'), nullable=True)

    subject_id = Column(Integer, ForeignKey('user.id'), nullable=True, index=True)
    object_id = Column(Integer, ForeignKey('user.id'), nullable=True, index=True)

    subject = relationship("User", foreign_keys=[subject_id], back_populates='subject_feedbacks')
    object_ = relationship("User", foreign_keys=[object_id], back_populates='object_feedbacks')

    offer = relationship('Offer', back_populates='feedbacks')

