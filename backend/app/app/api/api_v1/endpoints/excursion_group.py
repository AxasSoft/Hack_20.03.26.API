from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from fastapi.params import File, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....enums.mod_status import ModStatus
from ....exceptions import UnprocessableEntity, UnfoundEntity, InaccessibleEntity
from ....notification.notificator import Notificator
import logging

from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/excursions/{excursion_id}/groups/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionGroup],
    name="Получить экскурсионные группы",
    tags=["Административная панель / Экскурсии"]
)
@router.get(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/groups/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionGroup],
    name="Получить экскурсионные группы",
    tags=["Мобильное приложение / Экскурсии"]
)
def get_groups(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
        date: Optional[int] = Query(None, title="Дата"),
        members: Optional[int] = Query(None, title="Количество участников"),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    excursion = crud.excursion.get_by_id(db, id=excursion_id)
    if excursion is None:
        raise UnfoundEntity(
            message="Экскурсия не найдена"
        )
    data, paginator = crud.excursion_group.get_by_excursion(db=db, excursion=excursion, page=page, date=date, members=members)
    return schemas.ListOfEntityResponse(
        data=[
            getters.excursion_group.get_excursion_group(db=db, excursion_group=excursion_group)
            for excursion_group
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/excursions/{excursion_id}/groups/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionGroup],
    name="Создать экскурсионную группу",
    tags=["Административная панель / Экскурсии"]
)
def create_group(
        data: schemas.CreatingExcursionGroup,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
):
    excursion_group = crud.excursion_group.create(db, obj_in=data, excursion_id=excursion_id)
    return schemas.SingleEntityResponse(
        data=getters.excursion_group.get_excursion_group(db=db, excursion_group=excursion_group)
    )


@router.get(
    '/cp/excursions/groups/{group_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionGroup],
    name="Получить экскурсионную группу",
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
            'description': 'Группа не найдена'
        }
    },
    tags=["Административная панель / Экскурсии"]
)
@router.get(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/groups/{group_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionGroup],
    name="Получить экскурсионную группу",
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
            'description': 'Группа не найдена'
        }
    },
    tags=["Мобильное приложение / Экскурсии"]
)
def get_group(
        group_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    group = crud.excursion_group.get_by_id(db, id=group_id)
    if group is None:
        raise UnfoundEntity(
            message="Группа не найдена"
        )
    return schemas.SingleEntityResponse(data=getters.excursion_group.get_excursion_group(db=db, excursion_group=group))


@router.delete(
    '/cp/excursions/groups/{group_id}/',
    response_model=schemas.OkResponse,
    name="Удалить экскурсионную группу",
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
            'description': 'Группа не найдена'
        }
    },
    tags=["Административная панель / Экскурсии"]
)
def delete_group(
        group_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    group = crud.excursion_group.get_by_id(db, id=group_id)
    if group is None:
        raise UnfoundEntity(message="Группа не найдена", description="Группа не найдена",num=1)
    crud.excursion_group.remove(db, id=group_id)
    return schemas.OkResponse()


@router.post(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/groups/{group_id}/booking/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionBooking],
    name="Забронировать экскурсию",
    tags=["Мобильное приложение / Экскурсии"]
)
def create_booking(
        data: schemas.CreatingExcursionBooking,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        group_id: int = Path(..., title='Идентификатор группы'),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
):
    # booking_exists = crud.excursion_booking.get_by(db=db, group_id=group_id, user_id=current_user.id)
    # if booking_exists:
    #     return schemas.SingleEntityResponse(message="У вас уже есть бронирование на эту группу")
    new_booking = crud.excursion_booking.create_for_user(db, obj_in=data, group_id=group_id, user_id=current_user.id,
                                                         excursion_id=excursion_id)
    return schemas.SingleEntityResponse(
        data=getters.excursion_booking.get_excursion_booking(excursion_booking=new_booking)
    )


@router.put(
    '/cp/excursions/bookings/{booking_id}/status/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionBooking],
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
                'description': 'Группа не найдена'
            }
        },
    name="Обновить статус бронирования экскурсии",
    tags=["Административная панель / Бронирования"]
)
def update_booking_status(
        data: schemas.UpdatingStatusExcursionBooking,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        booking_id: int = Path(..., title='Идентификатор бронирования'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('excursion_booking_by_user')
    booking = crud.excursion_booking.get_by_id(db, id=booking_id)
    if booking is None:
        raise UnfoundEntity(
            message="Бронирование не найдено"
        )

    booking = crud.excursion_booking.update_status(db, status=data.status, booking=booking)
    return schemas.SingleEntityResponse(
        data=getters.excursion_booking.get_excursion_booking(excursion_booking=booking)
    )


@router.put(
    '/cp/excursions/groups/{group_id}/status/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionGroup],
    name="Обновить статус экскурсионной группы",
    tags=["Административная панель / Экскурсии"]
)
def create_booking(
        data: schemas.UpdatingStatusExcursionGroup,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        group_id: int = Path(..., title='Идентификатор группы'),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
):
    group = crud.excursion_group.get_by_id(db, id=group_id)
    if group is None:
        raise UnfoundEntity(message="Группа не найдена", description="Группа не найдена", num=1)
    group = crud.excursion_group.update_status(db, status=data.status, group=group)

    return schemas.SingleEntityResponse(
        data=getters.excursion_group.get_excursion_group(db=db, excursion_group=group)
    )