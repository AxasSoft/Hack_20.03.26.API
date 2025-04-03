from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.params import Path, File
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.exceptions import UnfoundEntity
from app.getters.achievement import get_achievement
from app.schemas.achievement import GettingUserAchievement

router = APIRouter()


@router.get(
    '/cp/achievements/',
    response_model=schemas.response.ListOfEntityResponse[schemas.achievement.GettingAchievement],
    name="Получить достижения",
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
    tags=["Панель управления / Достижения"]
)
def get_all_achievement(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        search: Optional[str] = Query(None),

        page: Optional[int] = Query(None)
):
    data, paginator = crud.crud_achievement.achievement.search(
        db=db,
        search=search,
        page=page
    )
    return schemas.response.ListOfEntityResponse(
        data=[
            getters.achievement.get_achievement(achievement=achievement)
            for achievement
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/achievements/',
    response_model=schemas.response.SingleEntityResponse[schemas.achievement.GettingAchievement],
    name="Создать достижение",
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
    tags=["Панель управления / Достижения"]
)
def create_achievement(
        data: schemas.achievement.CreatingAchievement,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
):
    achievement = crud.crud_achievement.achievement.create(
        db=db,
        obj_in=data,
    )

    return schemas.response.SingleEntityResponse(
        data=getters.achievement.get_achievement(achievement=achievement)
    )


@router.put(
    '/cp/achievements/{achievement_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.achievement.GettingAchievement],
    name="Изменить достижение",
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
    tags=["Панель управления / Достижения"]
)
def edit_achievement(
        data: schemas.achievement.UpdatingAchievement,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        achievement_id: int = Path(...)
):
    achievement = crud.crud_achievement.achievement.get_by_id(db=db, id=achievement_id)

    if achievement is None:
        raise UnfoundEntity(num=1, message='Достижение не найдено')

    achievement = crud.crud_achievement.achievement.update(
        db=db,
        db_obj=achievement,
        obj_in=data,
    )

    return schemas.response.SingleEntityResponse(
        data=getters.achievement.get_achievement(achievement=achievement)
    )


@router.put(
    '/cp/achievements/{achievement_id}/cover/',
    response_model=schemas.response.SingleEntityResponse[schemas.achievement.GettingAchievement],
    name="Изменить обложку достижения",
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
    tags=["Панель управления / Достижения"]
)
def edit_attachment(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        new_cover: Optional[UploadFile] = File(None),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        achievement_id: int = Path(...)
):
    achievement = crud.crud_achievement.achievement.get_by_id(db=db, id=achievement_id)
    if achievement is None:
        raise UnfoundEntity(num=1, message='Достижение не найдено')

    crud.crud_achievement.achievement.s3_client = s3_client
    crud.crud_achievement.achievement.s3_bucket_name = s3_bucket_name
    crud.crud_achievement.achievement.change_cover(db=db, achievement=achievement, new_cover=new_cover)
    return schemas.response.SingleEntityResponse(
        data=get_achievement(achievement=achievement)
    )


@router.delete(
    '/cp/achievements/',
    response_model=schemas.response.OkResponse,
    name="Удалить несколько достижений",
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
    tags=["Панель управления / Достижения"]
)
def delete_many_achievement(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        ids: List[int] = Query([])
):
    crud.crud_achievement.achievement.remove_many(db=db, ids=ids)

    return schemas.response.OkResponse()


@router.get(
    '/users/me/achievements/',
    response_model=schemas.response.ListOfEntityResponse[GettingUserAchievement],
    name="Получить достижения текущего пользователя",
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
    tags=["Мобильное приложение / Достижения"]
)
def get_user_achievement(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
):
    data = crud.crud_achievement.achievement.get_user_achievements(
        db=db,
        user=current_user,
    )
    return schemas.response.ListOfEntityResponse(
        data=data,
        meta=schemas.response.Meta(paginator=None)
    )


@router.get(
    '/cp/users/{user_id}/achievements/',
    response_model=schemas.response.ListOfEntityResponse[schemas.achievement.GettingUserAchievement],
    name="Получить достижения пользователя",
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
    tags=["Панель управления / Достижения"]
)
@router.get(
    '/users/{user_id}/achievements/',
    response_model=schemas.response.ListOfEntityResponse[schemas.achievement.GettingUserAchievement],
    name="Получить достижения пользователя",
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
    tags=["Мобильное приложение / Достижения"]
)
def get_user_achievement(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
        user_id: int = Path(...)
):
    user = crud.crud_user.user.get_by_id(
        db=db,
        id=user_id
    )
    if user is None:
        raise UnfoundEntity(num=1, message="Пользователь не найден")

    data = crud.crud_achievement.achievement.get_user_achievements(
        db=db,
        user=user,
    )
    return schemas.response.ListOfEntityResponse(
        data=data,
        meta=schemas.response.Meta(paginator=None)
    )



