from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from fastapi.params import File, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....exceptions import UnprocessableEntity, UnfoundEntity, InaccessibleEntity
from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/restaurants/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingRestaurant],
    name="Получить все доступные рестораны",
    tags=["Административная панель / Рестораны"]
)
@router.get(
    '/restaurants/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingRestaurant],
    name="Получить все доступные рестораны",
    tags=["Мобильное приложение / Рестораны"]
)
def get_all(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    data, paginator = crud.restaurant.get_multi(db=db, page=page)
    return schemas.ListOfEntityResponse(
        data=[
            getters.restaurant.get_restaurant(db=db, restaurant=restaurant)
            for restaurant
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/restaurants/',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurant],
    name="Добавить ресторан",
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
    tags=["Административная панель / Рестораны"]
)
def create_restaurant(
        data: schemas.CreatingRestaurant,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    restaurant = crud.restaurant.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.restaurant.get_restaurant(restaurant=restaurant, db=db)
    )


@router.put(
    '/cp/restaurants/{restaurant_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurant],
    name="Изменить ресторан",
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
            'description': 'Ресторан не найден'
        }
    },
    tags=["Административная панель / Рестораны"]
)
def edit_restaurant(
        data: schemas.UpdatingRestaurant,
        restaurant_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    restaurant = crud.restaurant.get_by_id(db, id=restaurant_id)
    if restaurant is None:
        raise UnfoundEntity(
            message="Ресторан не найден"
        )
    restaurant = crud.restaurant.update(db, db_obj=restaurant, obj_in=data)
    return schemas.SingleEntityResponse(data=getters.restaurant.get_restaurant(db=db, restaurant=restaurant))


@router.get(
    '/cp/restaurants/{restaurant_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurant],
    name="Получить ресторан",
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
            'description': 'Ресторан не найден'
        }
    },
    tags=["Административная панель / Рестораны"]
)
@router.get(
    '/restaurants/{restaurant_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurant],
    name="Получить ресторан",
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
            'description': 'Ресторан не найден'
        }
    },
    tags=["Мобильное приложение / Рестораны"]
)
def get_restaurant(
        restaurant_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    restaurant = crud.restaurant.get_by_id(db, id=restaurant_id)
    if restaurant is None:
        raise UnfoundEntity(
            message="Ресторан не найден"
        )
    return schemas.SingleEntityResponse(data=getters.restaurant.get_restaurant(restaurant=restaurant, db=db))




@router.delete(
    '/cp/restaurants/{restaurant_id}/',
    response_model=schemas.OkResponse,
    name="Удалить ресторан",
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
            'description': 'Ресторан не найден'
        }
    },
    tags=["Административная панель / Рестораны"]
)
def delete_restaurant(
        restaurant_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    restaurant = crud.restaurant.get_by_id(db, id=restaurant_id)
    if restaurant is None:
        raise UnfoundEntity(message="Ресторан не найден", description="Ресторан не найден",num=1)
    crud.restaurant.remove(db, id=restaurant_id)
    return schemas.OkResponse()


@router.post(
    '/cp/restaurants/{restaurant_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.restaurant.GettingRestaurant],
    name="Добавить изображение к ресторану",
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
    tags=["Административная панель / Рестораны"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        image: UploadFile = File(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        restaurant_id: int = Path(..., title='Идентификатор ресторана'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    restaurant = crud.crud_restaurant.restaurant.get_by_id(db=db, id=restaurant_id)
    if restaurant is None:
        raise UnfoundEntity(num=1, message='Ресторан не найден')

    crud.crud_restaurant.restaurant.s3_client = s3_client
    crud.crud_restaurant.restaurant.s3_bucket_name = s3_bucket_name
    crud.crud_restaurant.restaurant.add_image(db=db, restaurant=restaurant, image=image)
    return schemas.response.SingleEntityResponse(
        data=getters.restaurant.get_restaurant(restaurant=restaurant, db=db)
    )


@router.delete(
    '/cp/restaurants/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.restaurant.GettingRestaurant],
    name="Удалить изображение ресторана",
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
    tags=["Административная панель / Рестораны"]
)
def delete_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        image_id: int = Path(..., title='Идентификатор ресторана'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    restaurant_image = crud.crud_restaurant.restaurant.get_image_by_id(db=db, id=image_id)
    if restaurant_image is None:
        raise UnfoundEntity(num=1, message='Картинка не найдена')

    
    crud.crud_restaurant.restaurant.s3_client = s3_client
    crud.crud_restaurant.restaurant.s3_bucket_name = s3_bucket_name
    crud.crud_restaurant.restaurant.delete_image(db=db, image=restaurant_image)
    return schemas.response.SingleEntityResponse(
        data=getters.restaurant.get_restaurant(db=db, restaurant=restaurant_image.restaurant)
    )


@router.post(
    '/cp/restaurants/{restaurant_id}/phone_numbers',
    response_model=schemas.SingleEntityResponse[schemas.GettingRestaurant],
    name="Добавить ресторану номер телефона",
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
            'description': 'Ресторан не найден'
        }
    },
    tags=["Административная панель / Рестораны"]
)
def add_restaurant_phone_numbers(
        number: str,
        restaurant_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    restaurant = crud.restaurant.get_by_id(db, id=restaurant_id)
    if restaurant is None:
        raise UnfoundEntity(
            message="Ресторан не найден"
        )
    restaurant = crud.restaurant.add_phone_numbers(db=db, restaurant=restaurant, number=number)
    return schemas.SingleEntityResponse(data=getters.restaurant.get_restaurant(db=db, restaurant=restaurant))
