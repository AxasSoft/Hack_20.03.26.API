from typing import Optional, List
from pydantic import BaseModel, Field

from .id_model import IdModel
from ..enums.excursion_booking_status import ExcursionBookingStatus
from .excursion_member import CreatingExcursionMember, GettingExcursionMember


class CreatingExcursionBooking(BaseModel):
    comment: Optional[str]
    members_info: List[CreatingExcursionMember]


class UpdatingExcursionBooking(BaseModel):
    pass


class GettingExcursionBooking(IdModel, BaseModel):
    excursion_group_id: int
    user_id: int
    status: Optional[ExcursionBookingStatus]
    started: int
    ended: Optional[int]
    created: int
    updated_at: int
    comment: Optional[str]
    excursion_id: int
    excursion_name: str
    members: Optional[List[GettingExcursionMember]]
    excursion_images: List[Optional[str]] = []


class UpdatingStatusExcursionBooking(BaseModel):
    status: Optional[ExcursionBookingStatus]