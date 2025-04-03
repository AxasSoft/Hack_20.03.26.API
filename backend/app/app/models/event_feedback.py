import datetime

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class EventFeedback(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    text = Column(String, nullable=True)
    answer_text = Column(String, nullable=True)
    rate = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='cascade'), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey('event.id', ondelete='cascade'), nullable=False, index=True)

    user = relationship("User", back_populates="event_feedbacks")
    event = relationship("Event", back_populates="event_feedbacks")