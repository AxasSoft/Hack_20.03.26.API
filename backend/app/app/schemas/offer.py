from typing import Optional

from pydantic import BaseModel

from app.schemas import GettingUser, GettingUserShortInfo
from .id_model import IdModel


class CreatingOffer(BaseModel):
    text: str
    type: Optional[str]
    address: Optional[str]


class UpdatingOffer(BaseModel):
    text: str
    type: Optional[str]
    address: Optional[str]


class GettingOffer(IdModel, BaseModel):
    created: int
    user: GettingUserShortInfo
    text: str
    order_id: int
    type: Optional[str]
    address: Optional[str]
    is_winner: Optional[bool]


class IsWinnerBody(BaseModel):
    is_winner: Optional[bool]

