from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class VerificationCode(Base):

    id = Column(Integer, primary_key=True, index=True)

    tel = Column(String, nullable=False)
    created = Column(DateTime(), nullable=False, default=datetime.utcnow)
    value = Column(String(), nullable=False)
    used = Column(Boolean(), nullable=False, default=False)
