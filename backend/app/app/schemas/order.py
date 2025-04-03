import enum
from typing import Optional, List

from app.schemas import GettingUserShortInfo, GettingUser, GettingCategory, GettingSubcategory, GettingImage
from pydantic import BaseModel, Field

from . import GettingStoryAttachment, GettingHashtag
from .id_model import IdModel
from ..enums.mod_status import ModStatus
from ..models.order import Stage


class CreatingOrder(BaseModel):
    title: Optional[str]
    body: Optional[str]
    deadline: Optional[int]
    profit: Optional[int]
    address: Optional[str]
    type: Optional[str]
    subcategory_id: Optional[int]
    is_auto_recreate: Optional[bool]
    lat: Optional[float]
    lon: Optional[float]


class UpdatingOrder(BaseModel):
    title: Optional[str]
    body: Optional[str]
    deadline: Optional[int]
    profit: Optional[int]
    address: Optional[str]
    type: Optional[str]
    subcategory_id: Optional[int]
    is_auto_recreate: Optional[bool]
    lat: Optional[float]
    lon: Optional[float]


class GettingOrder(IdModel, BaseModel):
    created: Optional[int]
    title: Optional[str]
    body: Optional[str]
    deadline: Optional[int]
    profit: Optional[int]
    stage: Stage
    user: GettingUser
    category: Optional[GettingCategory]
    subcategory: Optional[GettingSubcategory]
    address: Optional[str]
    type: Optional[str]
    is_block: bool = Field(False)
    block_comment: Optional[str] = Field(None)
    is_auto_recreate: bool
    lat: Optional[float]
    lon: Optional[float]
    images: List[GettingImage]
    is_favorite: Optional[bool]
    status: ModStatus
    moderation_comment: Optional[str]
    is_stopping: Optional[bool]
    count_favorite: Optional[int]
    views_counter: Optional[int]



class CreatingOffer(BaseModel):
    text: str


class UpdatingOffer(BaseModel):
    text: str


class GettingOffer(IdModel, BaseModel):
    created: int
    user: GettingUserShortInfo
    text: str
    order_id: int
    order: Optional[GettingOrder]
    is_winner: Optional[bool]


class IsWinnerBody(BaseModel):
    is_winner: Optional[bool]


class GettingOrderWithWinner(GettingOrder):
    win_offer: Optional[GettingOffer]


class BlockBody(BaseModel):
    is_block: bool
    comment: Optional[str]


class IsFavoriteBody(BaseModel):
    is_favorite: bool


class ModerationBody(BaseModel):
    status: ModStatus
    comment: Optional[str]