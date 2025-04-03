import enum
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class BaseAdvSlide(BaseModel):
    title: Optional[str]
    body: Optional[str]


class CreatingAdvSlide(BaseAdvSlide):
    adv_id: int


class UpdatingAdvSlide(BaseAdvSlide):
    adv_id: Optional[int]


class GettingAdvSlide(BaseAdvSlide):
    id: int
    img: Optional[str]
