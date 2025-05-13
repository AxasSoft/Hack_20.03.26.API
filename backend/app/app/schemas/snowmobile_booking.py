from typing import Optional, List

from pydantic import BaseModel, Field, validator

from .excursion_category import GettingExcursionCategory
from .excursion_review import GettingExcursionReview
from .id_model import IdModel
from . import GettingUserShortInfo


class CreatingSnowmobileBooking(BaseModel):
    snowmobile_quantity : int
    started: int
    ended: int
    comment: Optional[str]



class GettingSnowmobileBooking(IdModel, CreatingSnowmobileBooking):
    created: int
    user_id: int
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    tel: Optional[str]
