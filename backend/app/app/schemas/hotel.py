from typing import Optional, List

from pydantic import BaseModel, Field

from .id_model import IdModel


class RoomGuests(BaseModel):
    adults: int
    children: Optional[List[int]]


class SimpleSearchCriteria(BaseModel):
    checkin: int
    checkout: int
    guests: Optional[List[RoomGuests]]


class GettingHotelSearchInfo(BaseModel):
    hid: Optional[str]
    meal_included: Optional[bool]
    card_payment: Optional[bool]
    free_cancellation: Optional[bool]
    room_name: Optional[str]
    rate: Optional[float]
    currency: Optional[str]
    image: Optional[str]
    address: Optional[str]
    name: Optional[str]
    image: Optional[str]
