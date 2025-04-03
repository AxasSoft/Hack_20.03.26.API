from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/subcategories/',
    tags=['Административная панель / Подкатегории'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubcategory],
    name="Получить все доступные подкатегории",

)
@router.get(
    '/subcategories/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubcategory],
    name="Получить все доступные подкатегории",
    tags=['Мобильное приложение / Подкатегории'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        category_id: Optional[int] = Query(None)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.subcategory.get_subcategory(subcategory)
            for subcategory
            in crud.subcategory.search(db=db, page=None, category_id=category_id)[0]
        ]
    )


@router.post(
    '/cp/subcategories/',
    response_model=schemas.SingleEntityResponse[schemas.GettingSubcategory],
    name="Добавить подкатегорию",
    description="Добавить новую подкатегорию",
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
    tags=["Административная панель / Подкатегории"]
)
def create_subcategory(
        data: schemas.CreatingSubcategory,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    subcategory = crud.subcategory.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.subcategory.get_subcategory(subcategory)
    )


@router.put(
    '/cp/subcategories/{subcategory_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingSubcategory],
    name="Изменить подкатегорию",
    description="Изменить подкатегорию",
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
            'description': 'Подкатегория не найдена'
        }
    },
    tags=["Административная панель / Подкатегории"]
)
def edit_subcategory(
        data: schemas.UpdatingSubcategory,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        subcategory_id: int = Path(..., description="Идентификатор подкатегории")
):

    subcategory = crud.subcategory.get_by_id(db, subcategory_id)
    if subcategory is None:
        raise UnfoundEntity(
            message="Подкатегория не найдена"
        )
    subcategory = crud.subcategory.update(db, db_obj=subcategory, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.subcategory.get_subcategory(subcategory)
    )


@router.delete(
    '/cp/subcategories/{subcategory_id}/',
    response_model=schemas.OkResponse,
    name="Удалить подкатегорию",
    description="Удалить подкатегорию обсуждения",
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
            'description': 'Подкатегория не найдена'
        }
    },
    tags=["Административная панель / Подкатегории"]
)
def delete_subcategory(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        subcategory_id: int = Path(..., description="Идентификатор подкатегории")
):

    subcategory = crud.subcategory.get_by_id(db, subcategory_id)
    if subcategory is None:
        raise UnfoundEntity(
            message="Подкатегория не найдена"
        )

    crud.subcategory.remove(db=db, id=subcategory_id)

    return schemas.OkResponse()
