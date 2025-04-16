from typing import Optional

from pydantic import BaseModel, Field

from .id_model import IdModel


class CreatingExcursionReview(BaseModel):
    visit_date: int
    description: Optional[str]
    rating: Optional[int] = Field(None, gt=0, lt=6)


class UpdatingExcursionReview(BaseModel):
    description: Optional[str]


class GettingExcursionReview(IdModel, CreatingExcursionReview):
    created: int
    updated_at: int
    user_id: int
    first_name: str
    patronymic: str
    last_name: str


class GettingShortExcursionReview(IdModel, CreatingExcursionReview):
    pass