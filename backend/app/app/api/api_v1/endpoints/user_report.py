from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.post(
    '/users/{user_id}/reports/',
    response_model=schemas.OkResponse,
    name="Пожаловаться на пользователя",
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
    tags=["Мобильное приложение / Жалобы"]
)
def report_user(
        data: schemas.CreatingUserReport,
        user_id: int = Path(...,title="Идентификатор пользователя"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
):
    getting_user = crud.user.get_by_id(db, user_id)

    if getting_user is None:
        raise UnfoundEntity(num=2, message="Пользовательт не найден")

    crud.user_report.create_for_users(db, obj_in=data,subject=current_user,object_=getting_user)

    return schemas.OkResponse()


@router.get(
    '/cp/users/reports/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUserReport],
    name="Получить все жалобы на пользователей",
    tags=['Административная панель / Жалобы'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        }
    }
)
def get_list_of_user_reports(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
        page: Optional[int] = Query(1, title="Номер страницы"),
):
    data, paginator = crud.user_report.get_multi(db, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.user_report.get_user_report(
                db,
                datum
            )
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.put(
    '/cp/users/reports/{report_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUserReport],
    name="Изменить жалобу на пользователя",
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
            'description': 'Жалоба не найдена'
        },
    },
    tags=['Административная панель / Жалобы'],
)
def edit_user_report(
        data: schemas.UpdatingUserReport,
        report_id: int = Path(..., title="Идентификатор жалобы"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_active_superuser),
):
    getting_report = crud.user_report.get_by_id(db, report_id)

    if getting_report is None:
        raise UnfoundEntity(num=2, message="Жалоба не найдена")

    report = crud.user_report.update(db, obj_in=data,db_obj=getting_report)

    return schemas.SingleEntityResponse(
        data=getters.user_report.get_user_report(
                db,
                report
            )
    )
