from sqlalchemy import Column, Integer, String

from app.db.base_class import Base
from sqlalchemy import Column, Integer, String

from app.db.base_class import Base


class Counter(Base):
    id = Column(Integer, primary_key=True, index=True)
    value = Column(Integer(), nullable=True)
    platform = Column(String(), nullable=True)