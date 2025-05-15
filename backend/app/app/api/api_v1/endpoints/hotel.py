from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form, HTTPException
from fastapi.params import File, Path
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from app.schemas.hotel import RoomGuests
from app.services.etg_ostrovok_manager.etg_ostrovok_manager import ostrovok_manager
from ....enums.mod_status import ModStatus
from ....exceptions import UnprocessableEntity, UnfoundEntity, InaccessibleEntity
from ....notification.notificator import Notificator
import logging

from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/hotels/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
    name="Поиск отеля",
    description="""параметр guests: 2 - число взрослых /
2and10.14 - двое взрослых и двое детей 10 и 14 лет /
2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 10 лет""",
    tags=["Административная панель / Отели"]
)
@router.get(
    '/hotels/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
    name="Поиск отеля",
    description="""параметр guests: 2 - число взрослых /
2and10.14 - двое взрослых и двое детей 10 и 14 лет /
2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 7 лет""",
    tags=["Мобильное приложение / Отели"]
)
def get_hotels(
        page: Optional[int] = Query(None),
        # db: Session = Depends(deps.get_db),
        checkin: int = Query(..., title='Дата заезда'),
        checkout: int = Query(..., title='Дата выезда'),
        guests: str = Query(..., title="Количество гостей"),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    def parse_guests_query(guests_str: str = Query(...)) -> List[RoomGuests]:
        try:
            rooms = []
            for room_str in guests_str.split("-"):
                parts = room_str.split("and")
                adults = int(parts[0])
                children = list(map(int, parts[1].split("."))) if len(parts) > 1 else None
                rooms.append(RoomGuests(adults=adults, children=children))
            return rooms
        except Exception as e:
            raise HTTPException(400, f"Invalid format. Expected 'XandY.Z-XandY.Z', got '{guests_str}'. Error: {e}")

    gest_list = parse_guests_query(guests)
    data, paginator = ostrovok_manager.get_hotels(checkin=checkin, checkout=checkout, guests=gest_list, page=page)
    return schemas.ListOfEntityResponse(
        data=data,
        meta=schemas.response.Meta(paginator=paginator)
    )


# @router.get(
#     '/raw_hotels/{hotel_hid}/',
#     # response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Сырой запрос - Страница отеля",
#     description="""параметр guests: 2 - число взрослых /
# 2and10.14 - двое взрослых и двое детей 10 и 14 лет /
# 2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 7 лет""",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_get_hotel(
        # db: Session = Depends(deps.get_db),
        hotel_hid: int = Path(..., title="Идентификатор отеля"),
        checkin: int = Query(..., title='Дата заезда'),
        checkout: int = Query(..., title='Дата выезда'),
        guests: str = Query(..., title="Количество гостей"),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    resp =  ostrovok_manager.raw_get_hotel(checkin=checkin, checkout=checkout, guests=guests, hid=hotel_hid)
    return JSONResponse(content=resp)


# @router.get(
#     '/prebooking/',
#     # response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Сырой запрос - Пред бронирование",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_prebooking(
        # db: Session = Depends(deps.get_db),
        booking_hash: str = Query(..., title="Хэш брони"),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    resp =  ostrovok_manager.raw_prebooking(booking_hash=booking_hash)
    return JSONResponse(content=resp)


# @router.get(
#     '/prebooking23/',
#     name="Сырой запрос - Пред бронирование",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_prebooking():
    print('JOPA')
    return None


@router.get(
    '/cp/hotels/{hotel_hid}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingHotelBookingInfo],
    name="Страница отеля",
    description="""параметр guests: 2 - число взрослых /
2and10.14 - двое взрослых и двое детей 10 и 14 лет /
2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 10 лет""",
    tags=["Административная панель / Отели"]
)
@router.get(
    '/hotels/{hotel_hid}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingHotelBookingInfo],
    name="Страница отеля",
    description="""параметр guests: 2 - число взрослых /
2and10.14 - двое взрослых и двое детей 10 и 14 лет /
2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 7 лет""",
    tags=["Мобильное приложение / Отели"]
)
def get_hotel(
        # db: Session = Depends(deps.get_db),
        checkin: int = Query(..., title='Дата заезда'),
        checkout: int = Query(..., title='Дата выезда'),
        guests: str = Query(..., title="Количество гостей"),
        hotel_hid: int = Path(..., title="Идентификатор отеля"),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    hotel = ostrovok_manager.get_hotel(checkin=checkin, checkout=checkout, guests=guests, hid=hotel_hid)
    return schemas.SingleEntityResponse(data=hotel)