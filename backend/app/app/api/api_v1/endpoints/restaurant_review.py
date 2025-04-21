from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from fastapi.params import File, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....exceptions import UnprocessableEntity, UnfoundEntity, InaccessibleEntity
from ....notification.notificator import Notificator
import logging

from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/restaurants/{restaurant_id}/reviews/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingRestaurantReview],
    name="Получить отзывы на ресторан",
    tags=["Административная панель / Рестораны"]
)
@router.get(
    '/restaurants/{restaurant_id}/reviews/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingRestaurantReview],
    name="Получить отзывы на ресторан",
    tags=["Мобильное приложение / Рестораны"]
)
def get_reviews(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        restaurant_id: int = Path(..., title='Идентификатор рестрорана'),
        current_user: models.user.User = Depends(
                    deps.get_current_user
                ),
):
    restaurant = crud.restaurant.get_by_id(db, id=restaurant_id)
    if restaurant is None:
        raise UnfoundEntity(
            message="Ресторан не найден"
        )
    data, paginator = crud.restaurant_review.get_by_restaurant(db=db, restaurant=restaurant, page=page)
    return schemas.ListOfEntityResponse(
        data=[
            getters.restaurant_review.get_restaurant_review(restaurant_review)
            for restaurant_review
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/restaurants/{restaurant_id}/reviews/',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurantReview],
    name="Создать отзыв на ресторан",
    tags=["Административная панель / Рестораны"]
)
@router.post(
    '/restaurants/{restaurant_id}/reviews/',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurantReview],
    name="Создать отзыв на ресторан",
    tags=["Мобильное приложение / Рестораны"]
)
def create_review(
        data: schemas.CreatingRestaurantReview,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        restaurant_id: int = Path(..., title='Идентификатор ресторана'),
):
    restaurant_review_exists = crud.restaurant_review.get_by(db=db, restaurant_id=restaurant_id, user_id=current_user.id)
    if restaurant_review_exists:
        return schemas.SingleEntityResponse(message="Вы уже оставляли отзыв на этот ресторан")
    restaurant_review = crud.restaurant_review.create(db, obj_in=data, user_id=current_user.id, restaurant_id=restaurant_id)
    return schemas.SingleEntityResponse(
        data=getters.restaurant_review.get_restaurant_review(restaurant_review=restaurant_review)
    )


# @router.put(
#     '/cp/restaurants/{restaurant_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingRestaurant],
#     name="Изменить ресторан",
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
#             'description': 'Ресторан не найден'
#         }
#     },
#     tags=["Административная панель / Рестораны"]
# )
# def edit_restaurant(
#         data: schemas.UpdatingRestaurant,
#         restaurant_id: int = Path(...),
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
# ):
#     restaurant = crud.restaurant.get_by_id(db, id=restaurant_id)
#     if restaurant is None:
#         raise UnfoundEntity(
#             message="Ресторан не найден"
#         )
#     restaurant = crud.restaurant.update(db, db_obj=restaurant, obj_in=data)
#     return schemas.SingleEntityResponse(data=getters.restaurant.get_restaurant(db=db, restaurant=restaurant))


# @router.get(
#     '/cp/restaurants/{restaurant_id}/reviews/{review_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingRestaurantReview],
#     name="Получить отзыв на ресторан",
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
#             'description': 'Отзыв не найден'
#         }
#     },
#     tags=["Административная панель / Рестораны"]
# )
# @router.get(
#     '/restaurants/{restaurant_id}/reviews/{review_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingRestaurantReview],
#     name="Получить отзыв на ресторан",
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
#             'description': 'Отзыв не найден'
#         }
#     },
#     tags=["Мобильное приложение / Рестораны"]
# )
def get_review(
        review_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    review = crud.restaurant_review.get_by_id(db, id=review_id)
    if review is None:
        raise UnfoundEntity(
            message="Отзыв не найден"
        )
    return schemas.SingleEntityResponse(data=getters.restaurant_review.get_restaurant_review(restaurant_review=review))




@router.delete(
    '/cp/restaurants/{restaurant_id}/reviews/{review_id}/',
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
    tags=["Административная панель / Рестораны"]
)
def delete_review(
        review_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    review = crud.restaurant_review.get_by_id(db, id=review_id)
    if review is None:
        raise UnfoundEntity(message="Отзыв не найден", description="Отзыв не найден",num=1)
    crud.restaurant_review.remove(db, id=review_id)
    crud.restaurant.update_rating(db=db, restaurant_id=review.restaurant_id)
    return schemas.OkResponse()


