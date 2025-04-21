from typing import Optional, List

from pydantic import BaseModel, Field, validator

from .restaurant_review import GettingRestaurantReview
from .id_model import IdModel
from ..enums.restaurant_type import RestaurantType


class MultilineString(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            return v.replace('\r\n', '\n')
        raise ValueError("Must be a string")

class CreatingRestaurant(BaseModel):
    name: str
    description: Optional[MultilineString] = None
    address: str
    two_gis_url: str
    loyalty_program: bool = False
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    avg_check: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    work_hours_weekdays: Optional[str] = None
    work_hours_weekends: Optional[str] = None
    delivery: bool = False
    type: RestaurantType
    priority: Optional[int] = None


class UpdatingRestaurant(CreatingRestaurant):
    name: Optional[str]
    address: Optional[str]
    two_gis_url: Optional[str]
    loyalty_program: Optional[bool] = False
    delivery: Optional[bool] = False
    type: Optional[RestaurantType]



class GettingRestaurant(IdModel, CreatingRestaurant):
    total_reviews: int
    avg_rating: float
    phone_numbers: Optional[List[str]]
    images: Optional[List[str]] = []
    reviews: Optional[List[GettingRestaurantReview]]

