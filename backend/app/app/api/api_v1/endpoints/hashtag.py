from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.models import User
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/hashtags/',
    tags=['Административная панель / Хештеги'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingHashtag],
    name="Получить все доступные хештеги",

)
def get_all(
        db: Session = Depends(deps.get_db),
        search: Optional[str] = Query(None,title="текст хештега"),
        user: User = Depends(deps.get_current_active_superuser)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.hashtag.get_hashtag(db,hashtag)
            for hashtag
            in crud.hashtag.search(db=db, page=None, search=search)[0]
        ]
    )


@router.get(
    '/hashtags/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingHashtag],
    name="Получить все доступные хештеги",
    tags=['Мобильное приложение / Хештеги'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        search: Optional[str] = Query(None,title="текст хештега")
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.hashtag.get_hashtag(db,hashtag)
            for hashtag
            in crud.hashtag.search(db=db, page=None, search=search)[0]
        ]
    )



@router.post(
    '/cp/hashtags/',
    response_model=schemas.SingleEntityResponse[schemas.GettingHashtag],
    name="Добавить хештег",
    description="Добавить новый хешетег",
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
    tags=["Административная панель / Хештеги"]
)
def create_hashtag(
        data: schemas.CreatingHashtag,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    hashtag = crud.hashtag.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.hashtag.get_hashtag(db,hashtag)
    )


@router.put(
    '/cp/hashtags/{hashtag_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingHashtag],
    name="Изменить хештег",
    description="Изменить хештег",
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
            'description': 'Хештег не найден'
        }
    },
    tags=["Административная панель / Хештеги"]
)
def edit_hashtag(
        data: schemas.UpdatingHashtag,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        hashtag_id: int = Path(..., description="Идентификатор хештега")
):

    hashtag = crud.hashtag.get_by_id(db, hashtag_id)
    if hashtag is None:
        raise UnfoundEntity(
            message="Хештег не найден"
        )
    hashtag = crud.hashtag.update(db, db_obj=hashtag, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.hashtag.get_hashtag(db,hashtag)
    )


@router.delete(
    '/cp/hashtags/{hashtag_id}/',
    response_model=schemas.OkResponse,
    name="Удалить хештег",
    description="Удалить хештег",
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
            'description': 'Хештег не найден'
        }
    },
    tags=["Административная панель / Хештеги"]
)
def delete_hashtag(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        hashtag_id: int = Path(..., description="Идентификатор хештега")
):

    hashtag = crud.hashtag.get_by_id(db, hashtag_id)
    if hashtag is None:
        raise UnfoundEntity(
            message="Хештег не найдена"
        )

    crud.hashtag.remove(db=db, id=hashtag_id)

    return schemas.OkResponse()
