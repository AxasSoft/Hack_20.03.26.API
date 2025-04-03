import enum
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class BaseStorySlide(BaseModel):
    title: Optional[str]
    body: Optional[str]


class CreatingStorySlide(BaseStorySlide):
    story_id: int


class UpdatingStorySlide(BaseStorySlide):
    story_id: Optional[int]


class GettingStorySlide(BaseStorySlide):
    id: int
    img: Optional[str]
