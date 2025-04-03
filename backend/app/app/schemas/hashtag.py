import enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from .id_model import IdModel


class BaseHashtag(BaseModel):
    text: str


class GettingHashtag(IdModel, BaseHashtag):
    stories_count: int = Field(0, title="Количество историй")
    cover: Optional[str] = Field(None)

class CreatingHashtag(BaseHashtag):
    pass


class UpdatingHashtag(BaseHashtag):
    pass

