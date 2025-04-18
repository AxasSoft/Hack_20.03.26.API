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
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionReview],
    name="Получить отзывы на экскурсию",
    tags=["Административная панель / Экскурсии"]
)
@router.get(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionReview],
    name="Получить отзывы на экскурсию",
    tags=["Мобильное приложение / Экскурсии"]
)
def get_reviews(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
):
    excursion = crud.excursion.get_by_id(db, id=excursion_id)
    if excursion is None:
        raise UnfoundEntity(
            message="Экскурсия не найдена"
        )
    data, paginator = crud.excursion_review.get_by_excursion(db=db, excursion=excursion, page=page)
    print(data)
    return schemas.ListOfEntityResponse(
        data=[
            getters.excursion_review.get_excursion_review(excursion_review)
            for excursion_review
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionReview],
    name="Создать отзыв на экскурсию",
    tags=["Административная панель / Экскурсии"]
)
@router.post(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionReview],
    name="Создать отзыв на экскурсию",
    tags=["Мобильное приложение / Экскурсии"]
)
def create_review(
        data: schemas.CreatingExcursionReview,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        excursion_id: int = Path(..., title='Идентификатор экскурсии'),
):
    print("TUT")
    excursion_review = crud.excursion_review.create(db, obj_in=data, user_id=current_user.id, excursion_id=excursion_id)
    return schemas.SingleEntityResponse(
        data=getters.excursion_review.get_excursion_review(excursion_review=excursion_review)
    )


# @router.put(
#     '/cp/excursions/{excursion_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingExcursion],
#     name="Изменить экскурсию",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданны невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         },
#         403: {
#             'model': schemas.OkResponse,
#             'description': 'Отказанно в доступе'
#         },
#         404: {
#             'model': schemas.OkResponse,
#             'description': 'Экскурсия не найдена'
#         }
#     },
#     tags=["Административная панель / Экскурсии"]
# )
# def edit_excursion(
#         data: schemas.UpdatingExcursion,
#         excursion_id: int = Path(...),
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
# ):
#     excursion = crud.excursion.get_by_id(db, id=excursion_id)
#     if excursion is None:
#         raise UnfoundEntity(
#             message="Экскурсия не найдена"
#         )
#     excursion = crud.excursion.update(db, db_obj=excursion, obj_in=data)
#     return schemas.SingleEntityResponse(data=getters.excursion.get_excursion(db=db, excursion=excursion))


@router.get(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/{review_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionReview],
    name="Получить отзыв на экскурсию",
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
            'description': 'Отзыв не найден'
        }
    },
    tags=["Административная панель / Экскурсии"]
)
@router.get(
    '/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/{review_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionReview],
    name="Получить отзыв на экскурсию",
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
            'description': 'Отзыв не найден'
        }
    },
    tags=["Мобильное приложение / Экскурсии"]
)
def get_review(
        review_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    review = crud.excursion_review.get_by_id(db, id=review_id)
    if review is None:
        raise UnfoundEntity(
            message="Отзыв не найден"
        )
    return schemas.SingleEntityResponse(data=getters.excursion_review.get_excursion_review(excursion_review=review))




@router.delete(
    '/cp/excursion-categories/{category_id}/excursions/{excursion_id}/reviews/{review_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отзыв",
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
            'description': 'Отзыв не найден'
        }
    },
    tags=["Административная панель / Экскурсии"]
)
def delete_review(
        review_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    review = crud.excursion_review.get_by_id(db, id=review_id)
    if review is None:
        raise UnfoundEntity(message="Отзыв не найден", description="Отзыв не найден",num=1)
    crud.excursion_review.remove(db, id=review_id)
    crud.excursion.update_rating(db=db, excursion_id=review.excursion_id)
    return schemas.OkResponse()


