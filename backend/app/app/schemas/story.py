import enum
from typing import Optional, List

from app.schemas import GettingUserShortInfo
from pydantic import BaseModel, Field

from . import GettingStoryAttachment, GettingHashtag
from .id_model import IdModel


class CreatingStory(BaseModel):
    text: Optional[str]
    video: Optional[int]
    gallery: Optional[List[int]]
    is_private: Optional[bool] = Field(False)
    hashtags: List[str]


class UpdatingStory(BaseModel):
    text: Optional[str]
    video: Optional[int]
    gallery: Optional[List[int]]
    is_private: Optional[bool]
    hashtags: Optional[List[str]]


class BaseGettingStory(IdModel, BaseModel):
    created: int
    text: Optional[str]
    video: Optional[GettingStoryAttachment]
    gallery: List[GettingStoryAttachment]
    is_private: bool
    hashtags: List[GettingHashtag]
    views_count: int = 0
    viewed: Optional[bool] = None
    hugs_count: int = 0
    hugged: Optional[bool] = None
    is_favorite: Optional[bool] = None
    comments_count: int = 0
    is_comment: Optional[bool] = False

class GettingStory(BaseGettingStory):
    user: GettingUserShortInfo


class GettingUserStories(BaseModel):
    user: GettingUserShortInfo
    stories: List[BaseGettingStory]



class HugBody(BaseModel):
    hugs: bool = Field(..., title="Обнять",
                       description="Флаг, означающий поставновление(`true`) или снятие (`false`) отмеки \"Обнять\"")


class IsFavoriteBody(BaseModel):
    is_favorite: bool = Field(...)


class HidingBody(BaseModel):
    hiding: bool = Field(..., title="Скрыть", description="Флаг, означающий. скрыта ли история")
