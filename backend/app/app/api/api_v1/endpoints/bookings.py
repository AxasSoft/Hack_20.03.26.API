from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path, Header
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta, OkResponse
from app.enums.excursion_booking_status import ExcursionBookingStatus
from ....exceptions import UnprocessableEntity, UnfoundEntity, ListOfEntityError, InaccessibleEntity
import logging


from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/users/me/bookings/excursions/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionBooking],
    name="Получить бронирования экскурсий текущего пользователя",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Бронирования"]
)
def get_excursion_bookings_by_user(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):

    def fatch_stories():
        data, paginator = crud.excursion_booking.get_bookings_by_user(
            db,
            user=current_user,
            page=page)
        
        return schemas.ListOfEntityResponse(
            data=[getters.excursion_booking.get_excursion_booking(excursion_booking=booking) for booking in data],
            meta=Meta(paginator=paginator)
            )
    
    key_tuple = ('excursion_booking_by_user', f"user - {current_user.id} - page - {page}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_stories, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.get(
    '/cp/users/{user_id}/bookings/excursions/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionBooking],
    name="Получить бронирования экскурсий пользователя",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Административная панель / Бронирования"]
)
def get_excursion_bookings_by_user(
        db: Session = Depends(deps.get_db),
        user_id: int = Path(..., title="Идентификатор пользователя"),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    user = crud.user.get_by_id(db, id=user_id)
    if user is None:
        raise UnfoundEntity(message='Пользователь не найден', num=2)

    def fatch_stories():
        data, paginator = crud.excursion_booking.get_bookings_by_user(
            db,
            user=user,
            page=page)

        return schemas.ListOfEntityResponse(
            data=[getters.excursion_booking.get_excursion_booking(excursion_booking=booking) for booking in data],
            meta=Meta(paginator=paginator)
        )

    key_tuple = ('excursion_booking_by_user', f"user - {user.id} - page - {page}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_stories, ttl=7200)

    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.get(
    '/users/me/bookings/excursions/{excursion_booking_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionBooking],
    name="Получить бронирование",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Бронирование не найдено'
        }
    },
    tags=["Мобильное приложение / Бронирования"]
)
def get_excursion_booking_by_id(
        excursion_booking_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    excursion_booking = crud.excursion_booking.get_by_id(db, id=excursion_booking_id)
    if excursion_booking is None:
        raise UnfoundEntity(
            message="Бронирование экскурсии не найдено"
        )
    return schemas.SingleEntityResponse(data=getters.excursion_booking.get_excursion_booking(excursion_booking=excursion_booking))


@router.put(
    '/users/me/bookings/excursions/{excursion_booking_id}/cancel/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionBooking],
    name="Отменить бронирование",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Бронирование не найдено'
        }
    },
    tags=["Мобильное приложение / Бронирования"]
)
def cancel_excursion_booking(
        excursion_booking_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    excursion_booking = crud.excursion_booking.get_by_id(db, id=excursion_booking_id)
    if excursion_booking is None:
        raise UnfoundEntity(
            message="Бронирование экскурсии не найдено"
        )
    excursion_booking = crud.excursion_booking.update_status(db, status=ExcursionBookingStatus.REJECTED, booking=excursion_booking)
    cache.delete_by_prefix('excursion_booking_by_user')
    return schemas.SingleEntityResponse(data=getters.excursion_booking.get_excursion_booking(excursion_booking=excursion_booking))
