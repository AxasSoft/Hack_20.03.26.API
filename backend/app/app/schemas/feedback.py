from typing import Optional

from pydantic import BaseModel

from app.schemas import GettingUser, GettingUserShortInfo
from .id_model import IdModel


class CreatingFeedback(BaseModel):
    text: Optional[str]
    rate: Optional[int]


class UpdatingFeedback(BaseModel):
    text: Optional[str]
    rate: Optional[int]


class GettingFeedback(IdModel, BaseModel):
    created: int
    text: Optional[str]
    rate: Optional[int]
    user: GettingUserShortInfo
