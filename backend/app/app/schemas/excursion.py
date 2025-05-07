from typing import Optional, List

from pydantic import BaseModel, Field, validator

# from . import GettingExcursionCategory, GettingExcursionReview
from .excursion_category import GettingExcursionCategory
from .excursion_review import GettingExcursionReview
from .id_model import IdModel
from .image import GettingImage
from ..enums.excursion_status import ExcursionStatus
from ..enums.mod_status import ModStatus


class MultilineString(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            return v.replace('\r\n', '\n')
        raise ValueError("Must be a string")

class CreatingExcursion(BaseModel):
    name: str
    description: Optional[MultilineString] = None
    duration: Optional[float]
    address: Optional[str]
    tips: Optional[str]
    price: float
    current_price: Optional[float]
    max_height: Optional[float]
    min_height: Optional[float]
    route_length: Optional[float]
    max_group_size: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    total_reviews: Optional[int]
    avg_rating: Optional[float]
    priority: Optional[float]
    category_id: int


class UpdatingExcursion(CreatingExcursion):
    name: Optional[str]
    price: Optional[float]
    excursion_status: Optional[ExcursionStatus]



# class GettingEventMember(IdModel, BaseModel):
#     user: GettingUserShortInfo
#     status: AcceptingStatus


class GettingExcursion(IdModel, CreatingExcursion):
    category: Optional[GettingExcursionCategory]
    images: Optional[List[str]] = []
    reviews: Optional[List[GettingExcursionReview]]

