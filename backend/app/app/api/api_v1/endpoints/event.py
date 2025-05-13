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
from ....models.event_member import EventMember
from ....notification.notificator import Notificator
import logging

from app.utils.cache import Cache

router = APIRouter()


def adapt_status(statuses):
    if statuses is None:
        return None
    else:
        return [ModStatus(status) for status in statuses]


@router.get(
    '/events/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingEvent],
    name="Получить все мероприятия текущего пользователя",
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
    tags=["Мобильное приложение / Мероприятия"]
)
def get_events_by_user(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(None, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_user),
        name: Optional[str] = Query(None),
        user_id: Optional[int] = Query(None),
        started_from: Optional[int] = Query(None),
        started_to: Optional[int] = Query(None),
        ended_from: Optional[int] = Query(None),
        ended_to: Optional[int] = Query(None),
        distance: Optional[int] = Query(None),
        lat: Optional[float] = Query(None),
        lon: Optional[float] = Query(None),
        is_private: Optional[bool] = Query(None),
        price_from: Optional[int] = Query(None),
        price_to: Optional[int] = Query(None),
        creator_id: Optional[int] = Query(None),
        place: Optional[str] = Query(None),
        is_open: Optional[bool] = Query(None),
        interests: Optional[List[int]] = Query(None),
        is_periodic: Optional[bool] = Query(None),
        reversed_order: Optional[bool] = True,
        collapse: Optional[bool] = True,
        statuses: Optional[List[int]] = Query(None),
        cache: Cache = Depends(deps.get_cache_list),
):
    
    def fatch_stories():
        data, paginator = crud.event.search(
            db,
            page=page,
            current_user=current_user,
            name=name,
            user_id=user_id,
            started_from=started_from,
            started_to=started_to,
            ended_from=ended_from,
            ended_to=ended_to,
            distance=distance,
            current_lat=lat,
            current_lon=lon,
            is_private=is_private,
            price_from=price_from,
            price_to=price_to,
            place=place,
            for_su=True,  # Для получения всех мероприятий пользователем
            creator_id=creator_id,
            is_open=is_open,
            interests=interests,
            is_periodic=is_periodic,
            reversed_order=reversed_order,
            collapse=collapse,
            statuses=adapt_status(statuses)
        )
        return schemas.ListOfEntityResponse(
            data=[
                getters.event.get_event(db, event=datum, current_user=current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )

    key_tuple = ('event_by_user', f"user - {current_user.id} - page - {page} \
                 - user_id - {user_id} - started_from - {started_to} - ended_from - {ended_from} - \
                    ended_to - {ended_to} - distance - {distance} - current_lat - {lat} - \
                        current_lon - {lon} - is_private - {is_private} - price_from - {price_from} - \
                            price_to - {price_to} - place - {place} - creator_id - {creator_id} - is_open - {is_open} - \
                                interests - {interests} - is_periodic - {is_periodic} - reversed_order - {reversed_order} - \
                                    collapse - {collapse} - statuses - {adapt_status(statuses)}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_stories, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.post(
    '/events/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEvent],
    name="Добавить мероприятие текущего пользователя",
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
    tags=["Мобильное приложение / Мероприятия"]
)
def create_event(
        data: schemas.CreatingEvent,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.create_for_user(db, obj_in=data, user=current_user, notificator=notificator) #notificator=notificator

    return schemas.SingleEntityResponse(
        data=getters.event.get_event(event=event, db=db,current_user=current_user)
    )


@router.put(
    '/events/{event_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEvent],
    name="Изменить мероприятие",
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
            'description': 'ХПользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def edit_profile_story(
        data: schemas.UpdatingEvent,
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.get_by_id(db, id=event_id)
    if event is None:
        raise UnfoundEntity(message="Мероприятие не найдено",description="Мероприятие не найдено",num=1)
    if event.user != current_user:
        raise InaccessibleEntity(
            message="Мероприятие не принадлежит порльзователю",
            description="Мероприятие не принадлежит порльзователю"
        )
    event = crud.event.update(db, db_obj=event, obj_in=data)
    return schemas.SingleEntityResponse(data=getters.event.get_event(db=db, event=event, current_user=current_user))


@router.get(
    '/events/{event_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEvent],
    name="Получить событие",
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
    tags=["Мобильное приложение / Мероприятия"]
)
def edit_profile_story(
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_optional_current_user),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def fatch_stories_single():
        event = crud.event.get_by_id(db, id=event_id)
        if event is None:
            raise UnfoundEntity(message="Мероприятие не найдено",description="Мероприятие не найдено",num=1)
        return schemas.SingleEntityResponse(data=getters.event.get_event(event=event, db=db, current_user=current_user))

    key_tuple = ('event_by_user', f"user - {current_user.id} - event_id - {event_id}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_stories_single, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data



@router.delete(
    '/events/{event_id}/',
    response_model=schemas.OkResponse,
    name="Удалить мероприятие",
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
            'description': 'ХПользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def delete_profile_story(
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.get_by_id(db, id=event_id)
    if event is None:
        raise UnfoundEntity(message="Мероприятие не найдено", description="Мероприятие не найдено",num=1)
    if event.user != current_user:
        raise InaccessibleEntity(
            message="Мероприятие не принадлежит порльзователю",
            description="Мероприятие не принадлежит порльзователю"
        )
    crud.event.remove(db, id=event_id)
    return schemas.OkResponse()


@router.put(
    '/events/members/{event_member_id}/status/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEventMember],
    name="Изменить статус участия в мероприятии",
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
            'description': 'ХПользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def edit_profile_story(
        data: schemas.StatusBody,
        event_member_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event_member = db.query(EventMember).get(event_member_id)
    if event_member is None:
        raise UnfoundEntity(message="Заявка не найдена", description="Заявка не найдена",num=1)
    if event_member.user != current_user:
        raise InaccessibleEntity(
            message="Заявка не принадлежит пользователю",
            description="Заявка не принадлежит пользователю"
        )
    event_member = crud.event.edit_member_status(db=db, event_member=event_member, new_status=data.status)
    return schemas.SingleEntityResponse(data=getters.event.get_event_member(event_member))


@router.get(
    '/cp/events/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingEvent],
    name="Получить все мероприятия",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказано в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
def get_events_by_user(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(None, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        name: Optional[str] = Query(None),
        user_id: Optional[int] = Query(None),
        started_from: Optional[int] = Query(None),
        started_to: Optional[int] = Query(None),
        is_private: Optional[bool] = Query(None),
        is_open: Optional[bool] = Query(None),
        interests: Optional[List[int]] = Query(None),
        is_periodic: Optional[bool] = Query(None),
        reversed_order: Optional[bool] = Query(False),
        statuses: Optional[List[str]] = Query(None),
):

    data, paginator = crud.event.search(
        db,
        page=page,
        current_user=current_user,
        name=name,
        user_id=user_id,
        started_from=started_from,
        started_to=started_to,
        is_private=is_private,
        for_su=True,
        is_open=is_open,
        interests=interests,
        is_periodic=is_periodic,
        reversed_order=reversed_order,
        statuses=adapt_status(statuses)
    )

    return schemas.ListOfEntityResponse(
        data=[
            getters.event.get_event(event=datum,db=db,current_user=current_user)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/cp/events/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEvent],
    name="Добавить мероприятия текущего пользователя",
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
    tags=["Панель управления / Мероприятия"]
)
def create_event(
        data: schemas.CreatingEvent,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.create_for_user(db, obj_in=data, user=current_user, notificator=notificator)

    return schemas.SingleEntityResponse(
        data=getters.event.get_event(event=event, db=db,current_user=current_user)
    )


@router.put(
    '/cp/events/{event_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEvent],
    name="Изменить мероприятие",
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
            'description': 'ХПользователь не найден'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
def edit_profile_story(
        data: schemas.UpdatingEvent,
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.get_by_id(db, id=event_id)
    if event is None:
        raise UnfoundEntity(message="Мероприятие не найдено",description="Мероприятие не найдено",num=1)
    event = crud.event.update(db, db_obj=event, obj_in=data)
    return schemas.SingleEntityResponse(data=getters.event.get_event(event=event, db=db,current_user=current_user))


@router.delete(
    '/cp/events/{event_id}/',
    response_model=schemas.OkResponse,
    name="Удалить мероприятие",
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
            'description': 'Мероприятие не найдено'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
def delete_profile_story(
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.get_by_id(db, id=event_id)
    if event is None:
        raise UnfoundEntity(message="Мероприятие не найдено", description="Мероприятие не найдено",num=1)
    crud.event.remove(db, id=event_id)
    return schemas.OkResponse()


@router.post(
    '/events/{event_id}/members/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEventMember],
    name="добавить участника в мероприятие",
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
    tags=["Мобильное приложение / Мероприятия"]
)
def add_event_member(
        data: schemas.CreatingEventMember,
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.event.get_by_id(db, id=event_id)
    if event is None:
        raise UnfoundEntity(message="Мероприятие не найдено",description="Мероприятие не найдено",num=1)

    if crud.event.member_exist(db, event_id=event_id, user_id=data.user_id):
        raise UnprocessableEntity(message="Участник уже добавлен")

    event_member = crud.event.add_member(db, event_id=event_id, user_id=data.user_id, status=data.status)

    return schemas.SingleEntityResponse(data=getters.event.get_event_member(event_member=event_member))


@router.delete(
    '/events/members/{member_id}/',
    response_model=schemas.OkResponse,
    name="Удалить участника из мероприятия",
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
            'description': 'Мероприятие не найдено'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def delete_profile_story(
        member_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event_member = crud.event.get_member(db, event_member_id=member_id)
    if event_member is None:
        raise UnfoundEntity(message="Участник не найден", description="Мероприятие не найдено",num=1)
    if event_member.user_id != current_user.id and event_member.event.user_id != current_user.id:
        raise InaccessibleEntity(message="У вас нет доступа", description="У вас нет доступа",num=1)

    crud.event.delete_member(db, event_member=event_member)

    return schemas.OkResponse()


@router.post(
    '/events/{event_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.event.GettingEvent],
    name="Добавить изображение в мероприятия",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        image: UploadFile = File(...),
        num: Optional[int] = Form(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        event_id: int = Path(..., title='Идентификатор мероприятия'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.crud_event.event.get_by_id(db=db, id=event_id)
    if event is None:
        raise UnfoundEntity(num=1, message='Мероприятия не найдена')

    crud.crud_event.event.s3_client = s3_client
    crud.crud_event.event.s3_bucket_name = s3_bucket_name
    crud.crud_event.event.add_image(db=db, event=event, image=image,num=num)
    event.is_accepted = None
    db.add(event)
    db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.event.get_event(event=event, db=db, current_user=current_user)
    )


@router.post(
    '/cp/events/{event_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.event.GettingEvent],
    name="Добавить изображение в мероприятие",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Мероприятия"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        image: UploadFile = File(...),
        num: Optional[int] = Form(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        event_id: int = Path(..., title='Идентификатор мероприятие'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event = crud.crud_event.event.get_by_id(db=db, id=event_id)
    if event is None:
        raise UnfoundEntity(num=1, message='Мероприятие не найдено')

    crud.crud_event.event.s3_client = s3_client
    crud.crud_event.event.s3_bucket_name = s3_bucket_name
    crud.crud_event.event.add_image(db=db, event=event, image=image, num=num)
    event.is_accepted = None
    db.add(event)
    db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.event.get_event(event=event, db=db,current_user=current_user)
    )


@router.delete(
    '/events/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.event.GettingEvent],
    name="Удалить изображение мероприятия",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Мобильное приложение / Мероприятия"]
)
@router.delete(
    '/cp/events/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.event.GettingEvent],
    name="Удалить изображение объявления",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Мероприятия"]
)
def delete_image(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        image_id: int = Path(..., title='Идентификатор мероприятия'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('event_by_user')
    event_image = crud.crud_event.event.get_image_by_id(db=db, id=image_id)
    if event_image is None:
        raise UnfoundEntity(num=1, message='Картинка не найдена')

    
    crud.crud_event.event.s3_client = s3_client
    crud.crud_event.event.s3_bucket_name = s3_bucket_name
    crud.crud_event.event.delete_image(db=db, image=event_image)
    return schemas.response.SingleEntityResponse(
        data=getters.event.get_event(db=db, event=event_image.event, current_user=current_user)
    )



@router.put(
    '/cp/events/{event_id}/moderation/',
    response_model=schemas.response.SingleEntityResponse[
        schemas.event.GettingEvent],
    name="Перевсти в другой статус / модератор",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Мероприятия"]
)
def edit_event(
        data: schemas.event.ModerationBody,
        event_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_active_superuser),
):

    event = crud.crud_event.event.get_by_id(db=db, id=event_id)

    if event is None:
        raise UnfoundEntity(num=1, message='Мероприятие не найдено')

    crud.crud_event.event.moderate(
        db=db,
        event=event,
        moderation_body=data
    )

    return schemas.response.SingleEntityResponse(
        data=getters.event.get_event(event=event)
    )

@router.get(
    '/cp/events/stats/',
    response_model=schemas.response.SingleEntityResponse[schemas.event.GettingEventStats],
    name="Получить статистику мероприятий",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Мероприятия"]
)
def statistic_event(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_active_superuser
        ),
):
    data = crud.crud_event.event.get_event_stat(db=db)

    return schemas.response.SingleEntityResponse(
        data=data
    )


@router.get(
    '/cp/events/stats/members/',
    # response_model=schemas.response.SingleEntityResponse[schemas.event.GettingEventStats],
    name="Получить статистику посещений мероприятий",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Мероприятия"]
)
def get_members_count(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_active_superuser)
):
    data = crud.crud_event.event.get_members_count(db=db)

    return schemas.response.SingleEntityResponse(
        data=data
    )