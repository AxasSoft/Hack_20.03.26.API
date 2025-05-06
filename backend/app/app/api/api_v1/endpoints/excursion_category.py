from fastapi import APIRouter, Depends, UploadFile, Query
from fastapi.params import Path, File
from sqlalchemy.orm import Session
from typing import Optional

from botocore.client import BaseClient
from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/excursion-categories/',
    tags=['Административная панель / Категории экскурсий'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionCategory],
    name="Получить все доступные категории",

)
@router.get(
    '/excursion-categories/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionCategory],
    name="Получить все доступные категории экскурсий",
    tags=['Мобильное приложение / Категории экскурсий'],
)
def get_all(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db)
):
    data, paginator = crud.excursion_category.get_multi(db=db, page=page)
    return schemas.ListOfEntityResponse(
        data=[
            getters.excursion_category.get_excursion_category(db=db, excursion_category=category)
            for category
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/excursion-categories/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionCategory],
    name="Добавить категорию",
    description="Добавить новую категорию",
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
        }
    },
    tags=["Административная панель / Категории экскурсий"]
)
def create_category(
        data: schemas.CreatingExcursionCategory,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    category = crud.excursion_category.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.excursion_category.get_excursion_category(db=db, excursion_category=category)
    )


@router.put(
    '/cp/excursion-categories/{category_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionCategory],
    name="Изменить категорию",
    description="Изменить категорию",
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
            'description': 'Категория не найдена'
        }
    },
    tags=["Административная панель / Категории экскурсий"]
)
def edit_category(
        data: schemas.UpdatingExcursionCategory,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        category_id: int = Path(..., description="Идентификатор категории")
):

    category = crud.excursion_category.get_by_id(db, category_id)
    if category is None:
        raise UnfoundEntity(
            message="Категория не найдена"
        )
    category = crud.excursion_category.update(db, db_obj=category, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.excursion_category.get_excursion_category(db=db, excursion_category=category)
    )


@router.delete(
    '/cp/excursion-categories/{category_id}/',
    response_model=schemas.OkResponse,
    name="Удалить категорию",
    description="Удалить категорию экскурсий",
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
            'description': 'Категория не найдена'
        }
    },
    tags=["Административная панель / Категории экскурсий"]
)
def delete_category(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        category_id: int = Path(..., description="Идентификатор категории")
):

    category = crud.excursion_category.get_by_id(db, category_id)
    if category is None:
        raise UnfoundEntity(
            message="Категория не найдена"
        )

    crud.excursion_category.remove(db=db, id=category_id)

    return schemas.OkResponse()

@router.post(
    '/cp/excursion-categories/{excursion_category_id}/image/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionCategory],
    name="Загрузить изоброражение категории",
    description="Добавить новую категорию",
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
        }
    },
    tags=["Административная панель / Категории экскурсий"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        image: UploadFile = File(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        excursion_category_id: int = Path(..., title='Идентификатор категории'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    excursion_category = crud.crud_excursion_category.excursion_category.get_by_id(db=db, id=excursion_category_id)
    if excursion_category is None:
        raise UnfoundEntity(num=1, message='Категория не найдена')

    crud.crud_excursion_category.excursion_category.s3_client = s3_client
    crud.crud_excursion_category.excursion_category.s3_bucket_name = s3_bucket_name
    crud.crud_excursion_category.excursion_category.add_image(db=db, excursion_category=excursion_category, image=image)
    # db.add(event)
    # db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.excursion_category.get_excursion_category(db=db, excursion_category=excursion_category)
    )

@router.delete(
    '/cp/excursion-categories/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.excursion_category.GettingExcursionCategory],
    name="Удалить изображение категории",
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
    tags=["Административная панель / Категории экскурсий"]
)
def delete_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        image_id: int = Path(..., title='Идентификатор изображения'),
):
    excursion_category_image = crud.crud_excursion_category.excursion_category.get_image_by_id(db=db, id=image_id)
    if excursion_category_image is None:
        raise UnfoundEntity(num=1, message='Картинка не найдена')
    crud.crud_excursion_category.excursion_category.s3_client = s3_client
    crud.crud_excursion_category.excursion_category.s3_bucket_name = s3_bucket_name
    crud.crud_excursion_category.excursion_category.delete_image(db=db, image=excursion_category_image)
    return schemas.response.SingleEntityResponse(
        data=getters.excursion_category.get_excursion_category(db=db, excursion_category=excursion_category_image.excursion_category)
    )
