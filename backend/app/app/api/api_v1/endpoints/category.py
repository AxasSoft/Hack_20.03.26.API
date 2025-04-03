from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()



@router.get(
    '/categories/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingCategory],
    name="Получить все доступные категории",
    tags=['Мобильное приложение / Категории'],
)
def get_all(
        db: Session = Depends(deps.get_db)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.category.get_category(category)
            for category
            in crud.category.get_multi(db=db, page=None)[0]
        ]
    )


@router.get(
    '/cp/categories/',
    tags=['Административная панель / Категории'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingCategoryWithSubcategories],
    name="Получить все доступные категории",

)
def get_all(
        db: Session = Depends(deps.get_db)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.category.get_category_with_subcategories(category)
            for category
            in crud.category.get_multi(db=db, page=None)[0]
        ]
    )


@router.post(
    '/cp/categories/',
    response_model=schemas.SingleEntityResponse[schemas.GettingCategory],
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
    tags=["Административная панель / Категории"]
)
def create_category(
        data: schemas.CreatingCategory,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    category = crud.category.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.category.get_category(category)
    )


@router.put(
    '/cp/categories/{category_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingCategory],
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
    tags=["Административная панель / Категории"]
)
def edit_category(
        data: schemas.UpdatingCategory,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        category_id: int = Path(..., description="Идентификатор категории")
):

    category = crud.category.get_by_id(db, category_id)
    if category is None:
        raise UnfoundEntity(
            message="Категория не найдена"
        )
    category = crud.category.update(db, db_obj=category, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.category.get_category(category)
    )


@router.delete(
    '/cp/categories/{category_id}/',
    response_model=schemas.OkResponse,
    name="Удалить категорию",
    description="Удалить категорию обсуждения",
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
    tags=["Административная панель / Категории"]
)
def delete_category(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        category_id: int = Path(..., description="Идентификатор категории")
):

    category = crud.category.get_by_id(db, category_id)
    if category is None:
        raise UnfoundEntity(
            message="Категория не найдена"
        )

    crud.category.remove(db=db, id=category_id)

    return schemas.OkResponse()
