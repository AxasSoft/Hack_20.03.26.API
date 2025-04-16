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
from ....models.excursion_participant import ExcursionParticipant
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
    '/cp/excursion-categories/{category_id}/excursions/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursion],
    name="Получить все доступные экскурсии",
    tags=["Административная панель / Экскурсии"]
)
@router.get(
    '/excursion-categories/{category_id}/excursions/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursion],
    name="Получить все доступные экскурсии",
    tags=["Мобильное приложение / Экскурсии"]
)
def get_all(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        category_id: int = Path(..., description="Идентификатор категории")
):
    data, paginator = crud.excursion.get_by_category(db=db, category_id=category_id, page=page)
    return schemas.ListOfEntityResponse(
        data=[
            getters.excursion.get_excursion(db=db, excursion=excursion)
            for excursion
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )
# def get_excursions_by_user(
#         db: Session = Depends(deps.get_db),
#         page: Optional[int] = Query(None, title="Номер страницы"),
#         current_user: models.User = Depends(deps.get_current_user),
#         name: Optional[str] = Query(None),
#         user_id: Optional[int] = Query(None),
#         started_from: Optional[int] = Query(None),
#         started_to: Optional[int] = Query(None),
#         ended_from: Optional[int] = Query(None),
#         ended_to: Optional[int] = Query(None),
#         distance: Optional[int] = Query(None),
#         lat: Optional[float] = Query(None),
#         lon: Optional[float] = Query(None),
#         is_private: Optional[bool] = Query(None),
#         price_from: Optional[int] = Query(None),
#         price_to: Optional[int] = Query(None),
#         creator_id: Optional[int] = Query(None),
#         place: Optional[str] = Query(None),
#         is_open: Optional[bool] = Query(None),
#         interests: Optional[List[int]] = Query(None),
#         is_periodic: Optional[bool] = Query(None),
#         reversed_order: Optional[bool] = True,
#         collapse: Optional[bool] = True,
#         statuses: Optional[List[int]] = Query(None),
#         cache: Cache = Depends(deps.get_cache_list),
# ):
#
#     def fatch_stories():
#         data, paginator = crud.excursion.search(
#             db,
#             page=page,
#             current_user=current_user,
#             name=name,
#             user_id=user_id,
#             started_from=started_from,
#             started_to=started_to,
#             ended_from=ended_from,
#             ended_to=ended_to,
#             distance=distance,
#             current_lat=lat,
#             current_lon=lon,
#             is_private=is_private,
#             price_from=price_from,
#             price_to=price_to,
#             place=place,
#             for_su=False,
#             creator_id=creator_id,
#             is_open=is_open,
#             interests=interests,
#             is_periodic=is_periodic,
#             reversed_order=reversed_order,
#             collapse=collapse,
#             statuses=adapt_status(statuses)
#         )
#         return schemas.ListOfEntityResponse(
#             data=[
#                 getters.excursion.get_excursion(db, excursion=datum, current_user=current_user)
#                 for datum
#                 in data
#             ],
#             meta=Meta(paginator=paginator)
#         )
#
#     key_tuple = ('excursion_by_user', f"user - {current_user.id} - page - {page} \
#                  - user_id - {user_id} - started_from - {started_to} - ended_from - {ended_from} - \
#                     ended_to - {ended_to} - distance - {distance} - current_lat - {lat} - \
#                         current_lon - {lon} - is_private - {is_private} - price_from - {price_from} - \
#                             price_to - {price_to} - place - {place} - creator_id - {creator_id} - is_open - {is_open} - \
#                                 interests - {interests} - is_periodic - {is_periodic} - reversed_order - {reversed_order} - \
#                                     collapse - {collapse} - statuses - {adapt_status(statuses)}")
#     data, from_cache = cache.behind_cache(key_tuple, fatch_stories, ttl=7200)
#
#     if from_cache:
#         logging.info("From the cache")
#     else:
#         logging.info("From the database")
#
#     return data


@router.post(
    '/cp/excursion-categories/{category_id}/excursions/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursion],
    name="Добавить экскурсию",
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
    },
    tags=["Административная панель / Экскурсии"]
)
def create_excursion(
        data: schemas.CreatingExcursion,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    excursion = crud.excursion.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.excursion.get_excursion(excursion=excursion, db=db)
    )


@router.put(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursion],
    name="Изменить экскурсию",
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
            'description': 'Экскурсия не найдена'
        }
    },
    tags=["Административная панель / Экскурсии"]
)
def edit_excursion(
        data: schemas.UpdatingExcursion,
        excursion_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    excursion = crud.excursion.get_by_id(db, id=excursion_id)
    if excursion is None:
        raise UnfoundEntity(
            message="Экскурсия не найдена"
        )
    excursion = crud.excursion.update(db, db_obj=excursion, obj_in=data)
    return schemas.SingleEntityResponse(data=getters.excursion.get_excursion(db=db, excursion=excursion))


@router.get(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursion],
    name="Получить экскурсию",
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
            'description': 'Экскурсия не найдена'
        }
    },
    tags=["Административная панель / Экскурсии"]
)
@router.get(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursion],
    name="Получить экскурсию",
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
            'description': 'Экскурсия не найдена'
        }
    },
    tags=["Мобильное приложение / Экскурсии"]
)
def get_excursion(
        excursion_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    excursion = crud.excursion.get_by_id(db, id=excursion_id)
    if excursion is None:
        raise UnfoundEntity(
            message="Экскурсия не найдена"
        )
    return schemas.SingleEntityResponse(data=getters.excursion.get_excursion(excursion=excursion, db=db))




@router.delete(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/',
    response_model=schemas.OkResponse,
    name="Удалить экскурсия",
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
    tags=["Административная панель / Экскурсии"]
)
def delete_excursion(
        excursion_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    excursion = crud.excursion.get_by_id(db, id=excursion_id)
    if excursion is None:
        raise UnfoundEntity(message="Экскурсия не найдена", description="Экскурсия не найдена",num=1)
    crud.excursion.remove(db, id=excursion_id)
    return schemas.OkResponse()


@router.post(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.excursion.GettingExcursion],
    name="Добавить изображение в экскурсию",
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
    tags=["Административная панель / Экскурсии"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        image: UploadFile = File(...),
        num: Optional[int] = Form(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    # cache.delete_by_prefix('excursion_by_user')
    excursion = crud.crud_excursion.excursion.get_by_id(db=db, id=excursion_id)
    if excursion is None:
        raise UnfoundEntity(num=1, message='Экскурсия не найдена')

    crud.crud_excursion.excursion.s3_client = s3_client
    crud.crud_excursion.excursion.s3_bucket_name = s3_bucket_name
    crud.crud_excursion.excursion.add_image(db=db, excursion=excursion, image=image, num=num)
    # excursion.is_accepted = None
    # db.add(excursion)
    # db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.excursion.get_excursion(excursion=excursion, db=db)
    )


@router.delete(
    '/cp/excursion-categories/{category_id}/excursions/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.excursion.GettingExcursion],
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
    tags=["Административная панель / Экскурсии"]
)
def delete_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        image_id: int = Path(..., title='Идентификатор экскурсии'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    # cache.delete_by_prefix('excursion_by_user')
    excursion_image = crud.crud_excursion.excursion.get_image_by_id(db=db, id=image_id)
    if excursion_image is None:
        raise UnfoundEntity(num=1, message='Картинка не найдена')

    
    crud.crud_excursion.excursion.s3_client = s3_client
    crud.crud_excursion.excursion.s3_bucket_name = s3_bucket_name
    crud.crud_excursion.excursion.delete_image(db=db, image=excursion_image)
    return schemas.response.SingleEntityResponse(
        data=getters.excursion.get_excursion(db=db, excursion=excursion_image.excursion)
    )



# @router.put(
#     '/cp/excursions/{excursion_id}/moderation/',
#     response_model=schemas.response.SingleEntityResponse[
#         schemas.excursion.GettingExcursion],
#     name="Перевсти в другой статус / модератор",
#     responses={
#         400: {
#             'model': schemas.response.OkResponse,
#             'description': 'Переданы невалидные данные'
#         },
#         422: {
#             'model': schemas.response.OkResponse,
#             'description': 'Переданы некорректные данные'
#         },
#         403: {
#             'model': schemas.response.OkResponse,
#             'description': 'Отказано в доступе'
#         },
#     },
#     tags=["Панель управления / Экскурсии"]
# )
# def edit_excursion(
#         data: schemas.excursion.ModerationBody,
#         excursion_id: int = Path(...),
#         db: Session = Depends(deps.get_db),
#         current_user: models.user.User = Depends(deps.get_current_active_superuser),
# ):
#
#     excursion = crud.crud_excursion.excursion.get_by_id(db=db, id=excursion_id)
#
#     if excursion is None:
#         raise UnfoundEntity(num=1, message='Экскурсия не найдена')
#
#     crud.crud_excursion.excursion.moderate(
#         db=db,
#         excursion=excursion,
#         moderation_body=data
#     )
#
#     return schemas.response.SingleEntityResponse(
#         data=getters.excursion.get_excursion(excursion=excursion)
#     )


