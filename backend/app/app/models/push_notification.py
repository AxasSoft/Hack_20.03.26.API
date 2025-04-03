from datetime import datetime

from sqlalchemy import Integer, Column, DateTime, String

from app.db.base_class import Base


class PushNotification(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime(), nullable=True, default=datetime.utcnow)
    title = Column(String(), nullable=True)
    body = Column(String(), nullable=True)
    link = Column(String(), nullable=True)