from typing import Optional

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, UploadFile
from fastapi.params import File, Path, Form
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnprocessableEntity, UnfoundEntity

router = APIRouter()


@router.post(
    '/stories/attachments/',
    response_model=schemas.SingleEntityResponse[schemas.GettingStoryAttachment],
    tags=['Мобильное приложение / Истории'],
    name="Загрузить новое изображение или видео для историй",
    responses={
        401: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не прошёл авторизацию'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },

    }
)
def upload(
        attachment: UploadFile = File(None),
        num: Optional[int] = Form(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
):

    crud.story_attachment.s3_client = s3_client
    crud.story_attachment.s3_bucket_name = s3_bucket_name

    attachment = crud.story_attachment.upload(
        db,
        current_user=current_user,
        attachment=attachment,
        num=num
    )

    if attachment is None:
        raise UnprocessableEntity(message="Не удалось загрузить файл", description="Не удалось загрузить файл")

    return schemas.SingleEntityResponse(
        data=getters.story_attachment.get_story_attachment(
            attachment
        )
    )



@router.post(
    '/cp/users/{user_id}/stories/attachments/',
    response_model=schemas.SingleEntityResponse[schemas.GettingStoryAttachment],
    tags=['Мобильное приложение / Истории'],
    name="Загрузить новое изображение или видео для историй",
    responses={
        401: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не прошёл авторизацию'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },

    }
)
def upload(
        attachment: UploadFile = File(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        user_id: int = Path(..., gt=0)
):

    user = crud.user.get_by_id(db, user_id)
    if user is None:
        raise UnfoundEntity(message="Пользователь не найден", description="Пользователь не найден")
    crud.story_attachment.s3_client = s3_client
    crud.story_attachment.s3_bucket_name = s3_bucket_name

    attachment = crud.story_attachment.upload(
        db,
        current_user=user,
        attachment=attachment
    )

    if attachment is None:
        raise UnprocessableEntity(message="Не удалось загрузить файл", description="Не удалось загрузить файл")

    return schemas.SingleEntityResponse(
        data=getters.story_attachment.get_story_attachment(
            attachment
        )
    )