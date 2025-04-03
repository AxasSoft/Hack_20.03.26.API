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
    '/stories/{story_id}/reports/',
    response_model=schemas.OkResponse,
    name="Пожаловаться на истоию",
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
            'description': 'История не найдена'
        }
    },
    tags=["Мобильное приложение / Жалобы"]
)
def report_user(
        data: schemas.CreatingStoryReport,
        story_id: int = Path(...,title="Идентификатор истории"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
):
    getting_story = crud.story.get_by_id(db, story_id)

    if getting_story is None:
        raise UnfoundEntity(num=2, message="История не найдена")

    crud.story_report.create_for_users(db, obj_in=data,subject=current_user,object_=getting_story)

    return schemas.OkResponse()


@router.get(
    '/cp/stories/reports/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingStoryReport],
    name="Получить все жалобы на истории",
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
def get_list_of_story_reports(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
        page: Optional[int] = Query(1, title="Номер страницы"),
):
    data, paginator = crud.story_report.get_multi(db, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.story_report.get_story_report(
                db,
                datum
            )
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.put(
    '/cp/stories/reports/{report_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingStoryReport],
    name="Изменить жалобу на историю",
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
def edit_story_report(
        data: schemas.UpdatingStoryReport,
        report_id: int = Path(..., title="Идентификатор жалобы"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_active_superuser),
):
    getting_report = crud.story_report.get_by_id(db, report_id)

    if getting_report is None:
        raise UnfoundEntity(num=2, message="Жалоба не найдена")

    report = crud.story_report.update(db, obj_in=data,db_obj=getting_report)

    return schemas.SingleEntityResponse(
        data=getters.story_report.get_story_report(
                db,
                report
            )
    )
