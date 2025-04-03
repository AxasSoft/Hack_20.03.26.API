from typing import Optional

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, UploadFile
from fastapi.params import File, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/pages/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingPage],
    name="Получить все страницы",
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
    tags=["Административная панель / Страницы"]
)
@router.get(
    '/pages/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingPage],
    name="Получить все страницы",
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
    tags=["Мобильное приложение/ Страницы"]
)
def get_pages_by_user(
        db: Session = Depends(deps.get_db),
        # current_user: models.User = Depends(deps.get_current_active_user),
):

    data, paginator = crud.page.get_multi(db,page=None)

    return schemas.ListOfEntityResponse(
        data=[
            getters.page.get_page(datum)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/cp/pages/',
    response_model=schemas.SingleEntityResponse[schemas.GettingPage],
    name="Добавить страницу",
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
    tags=["Административная панель / Страницы"]
)
def create_page(
        data: schemas.CreatingPage,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    page = crud.page.create(db,obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.get_page(page=page)
    )


@router.put(
    '/cp/pages/{page_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingPage],
    name="Изменить страницу",
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
    tags=["Административная панель / Страницы"]
)
def edit_page(
        data: schemas.UpdatingPage,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        page_id: int = Path(..., title='Идентификатор страницы')
):

    page = crud.page.get_by_id(db,id=page_id)
    if page is None:
        raise UnfoundEntity(num=1, message="Страница не найдена")

    page = crud.page.update(db, db_obj=page, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.get_page(page=page)
    )


@router.delete(
    '/cp/pages/{page_id}/',
    response_model=schemas.OkResponse,
    name="Удалить страницу",
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
    tags=["Административная панель / Страницы"]
)
def delete_page(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        page_id: int = Path(..., title='Идентификатор страницы')
):

    page = crud.page.get_by_id(db,id=page_id)
    if page is None:
        raise UnfoundEntity(num=1, message="Страница не найдена")

    crud.page.remove(db, id=page_id)

    return schemas.OkResponse()


@router.put(
    '/cp/pages/pdf/{slug}/',
    response_model=schemas.OkResponse,
    name="Загрузить pdf",
    description="Загружает pdf документ на сервер. После этого документ доступен "
                "по ссылке вида \"https://storage.yandexcloud.net/porto/documents/{slug}\" ",
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
    tags=["Административная панель / Страницы"]
)
def upload_pdf(
        file: Optional[UploadFile] = File(None),
        current_user: models.User = Depends(deps.get_current_active_user),
        slug: str = Path(..., title='Название страницы'),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
):
    crud.page.upload_pdf(slug, file, s3_bucket_name, s3_client)
    return schemas.OkResponse()
