from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field

from .id_model import IdModel


class RoomGuests(BaseModel):
    adults: int
    children: Optional[List[int]]


class SimpleSearchCriteria(BaseModel):
    checkin: int
    checkout: int
    guests: Optional[List[RoomGuests]]


class ComfortEnum(str, Enum):
    PARKING = "parking"
    INTERNET = "internet"
    POOL = "pool"
    TRANSFER = "transfer"
    ANIMALS = "animals"


class HotelDescriptionChapter(BaseModel):
    title: str
    paragraphs: List[str]


class HotelComfortChapter(BaseModel):
    title: str
    amenities: List[str]

    class Config:
        schema_extra = {
            "description": f'Заголовки удобств: "Бассейн и пляж", "Интернет", "Животные", "Парковка", "Трансфер", "Общее", "Питание", "В номерах"'
        }

class AvailableRoom(BaseModel):
    images: List[str]
    price: float
    room_name: str


class GettingHotelSearchInfo(BaseModel):
    hid: Optional[str]
    meal_included: Optional[bool]
    card_payment: Optional[bool]
    free_cancellation: Optional[bool]
    room_name: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    image: Optional[str]
    address: Optional[str]
    name: Optional[str]
    image: Optional[str]
    comfort: Optional[List[ComfortEnum]]


class GettingHotelBookingInfo(BaseModel):
    hid: Optional[str]
    images: Optional[List[str]]
    address: Optional[str]
    name: Optional[str]
    comfort: Optional[List[HotelComfortChapter]]
    description: Optional[List[HotelDescriptionChapter]]
    lat: Optional[float]
    lon: Optional[float]
    available_rooms: Optional[List[AvailableRoom]]


