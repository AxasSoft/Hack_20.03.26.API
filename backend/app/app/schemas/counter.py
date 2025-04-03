import enum
from typing import Optional, List

from app.schemas import GettingUserShortInfo
from pydantic import BaseModel, EmailStr, Field

from .id_model import IdModel



class CreatingCounter(BaseModel):
    platform: str


class UpdatingCounter(BaseModel):
    platform: Optional[str]
    value: Optional[int]

class GettingCounter(BaseModel):
    id: int
    platform: str
    value: int