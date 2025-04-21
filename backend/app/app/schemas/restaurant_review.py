from typing import Optional

from pydantic import BaseModel, Field

from .id_model import IdModel


class CreatingRestaurantReview(BaseModel):
    visit_date: int
    description: Optional[str]
    rating: Optional[int] = Field(None, gt=0, lt=6)


class UpdatingRestaurantReview(BaseModel):
    description: Optional[str]


class GettingRestaurantReview(IdModel, CreatingRestaurantReview):
    created: int
    updated_at: int
    user_id: int
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    avatar: Optional[str]