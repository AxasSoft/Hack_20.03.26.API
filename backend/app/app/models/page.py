import datetime
from typing import TYPE_CHECKING

from app.models import User
from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Page(Base):
    id = Column(Integer, primary_key=True, index=True)
    tech_name = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True, index=True)
    body = Column(String, nullable=True)