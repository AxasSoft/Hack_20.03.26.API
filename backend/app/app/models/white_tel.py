import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import User, Story


class WhiteTel(Base):
    id = Column(Integer, primary_key=True, index=True)
    tel = Column(String, index=True)
    name = Column(String, nullable=True)
    comment = Column(String, nullable=True)