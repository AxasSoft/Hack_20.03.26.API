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



# @router.get(
#     '/create_booking/',
#     # response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Сырой запрос - Создать бронирование",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_create_booking(
        # db: Session = Depends(deps.get_db),
        booking_hash: str = Query(..., title="Хэш брони"),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    resp =  ostrovok_manager.raw_create_booking(booking_hash=booking_hash)
    return JSONResponse(content=resp)


# @router.post(
#     '/create_credit_card_token/',
#     # response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Сырой запрос - Создать токен кредитной карты",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_create_credit_card_token(
        # db: Session = Depends(deps.get_db),
        object_id: str,
        user_first_name: str,
        user_last_name: str,
        is_cvc_required: bool,
        credit_card_data_core: schemas.CreditCardData,
        cvc: Optional[str] = None,
        current_user: models.User = Depends(deps.get_current_active_user)
):
    resp =  ostrovok_manager.raw_create_credit_card_token(
        object_id=object_id,
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        is_cvc_required=is_cvc_required,
        cvc=cvc,
        credit_card_data_core=credit_card_data_core
    )
    return JSONResponse(content=resp)


# @router.post(
#     '/raw_booking_hotel/',
#     # response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Сырой запрос - Забронировать отель",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_booking_hotel(
        # db: Session = Depends(deps.get_db),
        partner_order_id: str,
        payment_type: str,
        amount: str,
        currency_code: str,
        client: schemas.ClientBookingData,
        init_uuid: Optional[str] = None,
        pay_uuid: Optional[str] = None,
        current_user: models.User = Depends(deps.get_current_active_user)
):
    resp =  ostrovok_manager.raw_booking_hotel(
        partner_order_id=partner_order_id,
        payment_type=payment_type,
        amount=amount,
        currency_code=currency_code,
        client=client,
        init_uuid=init_uuid,
        pay_uuid=pay_uuid
    )
    return JSONResponse(content=resp)


# @router.get(
#     '/raw_check_booking/',
#     # response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Сырой запрос - Проверить бронирование",
#     tags=["Мобильное приложение / Отели"]
# )
def raw_check_booking(
        # db: Session = Depends(deps.get_db),
        partner_order_id: str = Query(..., title="бронь"),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    resp =  ostrovok_manager.raw_check_booking(partner_order_id=partner_order_id)
    return JSONResponse(content=resp)


# @router.get(
#     '/hotels_by_hids/',
#     response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
#     name="Поиск отелей по id",
#     description="""параметр guests: 2 - число взрослых /
# 2and10.14 - двое взрослых и двое детей 10 и 14 лет /
# 2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 7 лет""",
#     tags=["Мобильное приложение / Отели"]
# )
def get_hotels_by_hids(
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
    resp = ostrovok_manager.raw_search_by_hid(checkin=checkin, checkout=checkout, guests=gest_list)
    return JSONResponse(content=resp)


@router.get(
    '/test/',
    # response_model=schemas.SingleEntityResponse[schemas.GettingHotelBookingInfo],
    name="Страница тест-отеля",
    description="""параметр guests: 2 - число взрослых /
2and10.14 - двое взрослых и двое детей 10 и 14 лет /
2-3and7 - два номера в одном 2 взрослых, в другом 3 взрослых и ребенок 7 лет""",
    tags=["Мобильное приложение / Отели"]
)
def raw_get_test_hotel(
        # db: Session = Depends(deps.get_db),
        checkin: int = Query(..., title='Дата заезда'),
        checkout: int = Query(..., title='Дата выезда'),
        guests: str = Query(..., title="Количество гостей"),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    hotel = ostrovok_manager.raw_get_test_hotel(checkin=checkin, checkout=checkout, guests=guests)
    return schemas.SingleEntityResponse(data=hotel)


@router.get(
    '/set_bookings/',
    name="Сырой запрос - Бронирования",
    tags=["Мобильное приложение / Отели"]
)
def set_bookings(
        current_user: models.User = Depends(deps.get_current_active_user),
):
    resp = ostrovok_manager.raw_get_bookings()
    return schemas.SingleEntityResponse(data=resp)


@router.get(
    '/cancel_booking/',
    name="Бронирования",
    tags=["Мобильное приложение / Отели"]
)
def cancel_booking(
        partner_order_id: str,
        current_user: models.User = Depends(deps.get_current_active_user),
):
    resp = ostrovok_manager.cancel_booking(partner_order_id=partner_order_id)
    return schemas.SingleEntityResponse(data=resp)


@router.post(
    '/pay/',
    name="Оплата?",
    tags=["Мобильное приложение / Отели"]
)
def secure_check(
        url: str,
        data: schemas.ETGPayData,
        current_user: models.User = Depends(deps.get_current_active_user),
):
    data_dict = data.dict()
    # data_dict = {
    #     "MD": "2025051612473137524X",
    #     "PaReq": "eJxVUsluwjAQ/RXEPbHjxDFBgyUoh3IIRTQ99OgYF6KSBcehtF/fOEuhlizNe555sxmSk1Zq/apkoxWHWNW1OKpJdlhM/YjJiNLUEcxPnUCkgRNFlDhUCi9NqQyp9KYcdsu9unC4Kl1nZcE9F7sE0AhbRS1PojAchLysNlseEBIQCmiAkCu9WXOGccRwQHB/APU0FCJXvKyNLq/lp6sbQB0DsmwKo795GPiARgCNPvOTMVU9Ryivzs3R3D7cvDmbTAptRBdvfQDdy9o11qpbzVt24HEi8fYnpi/JuxcnsbddL7/i/i4AWQ84CKM4wYRi6oUTj84DNvc9QB0PIrfFcDILSehP9m+rttOegspmWj6+20YfWWi3oFUhx75GBOpWlYWycYD+bED32p+e7YClaWdGGMUzxhixEgNnBbJ2QiTCQadgASAbhYYFomH3rfXvT/wCAMCwng==",
    #     "termurl": "https://ostrovok.ru/secure/pay_complete_3ds/?payment_id=31070744&ret_path=http://109.73.199.21/api/v1/success"
    #   }
    resp = ostrovok_manager.secure_check(url=url, data=data_dict)
    return schemas.SingleEntityResponse(data=resp)


@router.post(
    '/start_booking_hotel/',
    response_model=schemas.SingleEntityResponse[schemas.CreatingBooking],
    name="Начать бронирование",
    tags=["Мобильное приложение / Отели"]
)
@router.post(
    '/cp/start_booking_hotel/',
    response_model=schemas.SingleEntityResponse[schemas.CreatingBooking],
    name="Начать бронирование",
    tags=["Административная панель / Отели"]
)
def start_booking(
        data: schemas.BookingHashData,
        checkin: int = Query(..., title='Дата заезда'),
        checkout: int = Query(..., title='Дата выезда'),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    new_hotel_booking = ostrovok_manager.create_booking(book_hash=data.book_hash,
                                           match_hash=data.match_hash,
                                           user_id=current_user.id,
                                           checkin=checkin,
                                           checkout=checkout,
                                           db=db
                                           )
    return schemas.SingleEntityResponse(data=new_hotel_booking)


@router.post(
    '/finish_booking_hotel/',
    response_model=schemas.SingleEntityResponse[schemas.CreatingBooking],
    name="Закончить бронирование",
    tags=["Мобильное приложение / Отели"]
)
@router.post(
    '/cp/finish_booking_hotel/',
    response_model=schemas.SingleEntityResponse[schemas.CreatingBooking],
    name="Закончить бронирование",
    tags=["Административная панель / Отели"]
)
def finish_booking(
        data: schemas.FinishBooking,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    hotel_booking = ostrovok_manager.booking_hotel(booking_id=data.booking_id,
                                           user_data=data.user_data,
                                           db=db
                                           )
    return schemas.SingleEntityResponse(data=hotel_booking)


@router.get(
    '/test_hotel_dump/',
    name="Дамп тест отеля",
    tags=["Мобильное приложение / Отели"]
)
def test_hotel_dump(
        current_user: models.User = Depends(deps.get_current_active_user),
):
    resp = ostrovok_manager.raw_get_test_hotel_dump()
    print(resp)
    return JSONResponse(content=resp)


