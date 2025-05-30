from typing import Optional, List, Any
from enum import Enum
from datetime import datetime, date

from pydantic import BaseModel, Field

from .id_model import IdModel
from .credit_card import CreditCardWithCvc
from app.enums.hotel_booking_status import HotelBookingStatus


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


class NotIncludedTax(BaseModel):
    name: str
    currency: str
    amount: int


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
    book_hash: str
    match_hash: str
    is_need_credit_card_data: bool
    is_payment_now: bool
    has_free_cancellation: bool
    free_cancellation_before: Optional[int]
    not_included_taxes: Optional[List[NotIncludedTax]]



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
    phone: Optional[str]
    email: Optional[str]
    name: Optional[str]
    comfort: Optional[List[HotelComfortChapter]]
    description: Optional[List[HotelDescriptionChapter]]
    lat: Optional[float]
    lon: Optional[float]
    available_rooms: Optional[List[AvailableRoom]]
    extra_info: Optional[str]


class ClientBookingData(BaseModel):
    first_name_original: str
    last_name_original: str
    phone: str
    email: str


class ETGPayData(BaseModel):
    MD: str
    PaReq: str
    TermUrl: str


class BookingHashData(BaseModel):
    book_hash: str
    match_hash: str


class PreCreatedBooking(BaseModel):
    hotel_hid: str
    hotel_name: str
    room_id: Optional[int]
    rg_ext_hash: int
    room_name: str
    has_free_cancellation: bool
    free_cancellation_before: Any  # Заменить на дату и вр


class CreatedBooking(BaseModel):
    price: float
    currency: str
    etg_pay_type: str
    item_id: int
    order_id: int
    partner_order_id: str
    checkin: date
    checkout: date
    user_id: int
    is_need_credit_card_data: bool
    is_need_cvc: bool


class CreatingBooking(BaseModel):
    booking_id: int
    is_need_credit_card_data: bool
    is_payment_now: bool


class BookingUserData(BaseModel):
    card_data: Optional[CreditCardWithCvc]
    first_name: str
    last_name: str
    phone: str
    email: str


class FinishBooking(BaseModel):
    booking_id: int
    user_data: BookingUserData


class GettingBooking(BaseModel):
    id: int
    created: int
    checkin: int
    checkout: int
    hotel_name: str
    room_name: str
    price: int
    status: HotelBookingStatus
    hotel_image: Optional[str]
    has_free_cancellation: bool
    free_cancellation_before: Optional[int]

class GettingDetailBooking(GettingBooking):
    hotel_image: Optional[List[str]]
    room_images: Optional[List[str]]
    not_included_taxes: Optional[List[NotIncludedTax]]








