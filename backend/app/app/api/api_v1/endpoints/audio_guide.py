from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from fastapi.params import File, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....enums.mod_status import ModStatus
from ....exceptions import UnprocessableEntity, UnfoundEntity, InaccessibleEntity
from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/audio_guides/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingAudioGuide],
    name="Получить все доступные аудиогиды",
    tags=["Административная панель / Аудиогиды"]
)
@router.get(
    '/audio_guides/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingAudioGuide],
    name="Получить все доступные аудиогиды",
    tags=["Мобильное приложение / Аудиогиды"]
)
def get_all(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    data, paginator = crud.audio_guide.get_page(db=db, page=page)
    return schemas.ListOfEntityResponse(
        data=[
            getters.audio_guide.get_audio_guide(audio_guide=audio_guide)
            for audio_guide
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/audio_guides/',
    response_model=schemas.SingleEntityResponse[schemas.GettingAudioGuide],
    name="Добавить аудиогид",
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
    tags=["Административная панель / Аудиогиды"]
)
def create_audio_guide(
        data: schemas.CreatingAudioGuide,
        db: Session = Depends(deps.get_db),
        # audio: UploadFile = File(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    crud.audio_guide.s3_client = s3_client
    crud.audio_guide.s3_bucket_name = s3_bucket_name
    audio_guide = crud.audio_guide.create(db=db, obj_in=data)

    return schemas.response.SingleEntityResponse(
        data=getters.audio_guide.get_audio_guide(audio_guide=audio_guide)
    )



@router.put(
    '/cp/audio_guides/{audio_guide_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingAudioGuide],
    name="Изменить аудиогид",
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
            'description': 'Экскурсия не найдена'
        }
    },
    tags=["Административная панель / Аудиогиды"]
)
def edit_audio_guide(
        data: schemas.UpdatingAudioGuide,
        audio_guide_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    audio_guide = crud.audio_guide.get_by_id(db, id=audio_guide_id)
    if audio_guide is None:
        raise UnfoundEntity(
            message="Аудиогид не найден"
        )
    excursion = crud.audio_guide.update(db, db_obj=audio_guide, obj_in=data)
    return schemas.response.SingleEntityResponse(
        data=getters.audio_guide.get_audio_guide(audio_guide=audio_guide)
    )


@router.delete(
    '/cp/audio_guides/{audio_guide_id}/',
    response_model=schemas.OkResponse,
    name="Удалить аудиогид",
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
            'description': 'ХПользователь не найден'
        }
    },
    tags=["Административная панель / Аудиогиды"]
)
def delete_excursion(
        audio_guide_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    audio_guide = crud.audio_guide.get_by_id(db, id=audio_guide_id)
    if audio_guide is None:
        raise UnfoundEntity(message="Аудиогид не найден", description="Аудиогид не найден",num=1)
    crud.audio_guide.remove(db, id=audio_guide_id)
    return schemas.OkResponse()


@router.post(
    '/cp/audio_guides/{audio_guide_id}/audios/',
    response_model=schemas.response.SingleEntityResponse[schemas.GettingAudioGuide],
    name="Добавить аудио в аудиогид",
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
    tags=["Административная панель / Аудиогиды"]
)
def add_audio(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        audio: UploadFile = File(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        audio_guide_id: int = Path(..., title='Идентификатор экскурсии'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    # cache.delete_by_prefix('excursion_by_user')
    audio_guide = crud.audio_guide.get_by_id(db=db, id=audio_guide_id)
    if audio_guide is None:
        raise UnfoundEntity(num=1, message='Аудиогид не найден')

    crud.audio_guide.s3_client = s3_client
    crud.audio_guide.s3_bucket_name = s3_bucket_name
    crud.audio_guide.add_audio(db=db, audio_guide=audio_guide, audio_file=audio)
    # excursion.is_accepted = None
    # db.add(excursion)
    # db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.audio_guide.get_audio_guide(audio_guide=audio_guide)
    )


@router.post(
    '/cp/audio_guides/{audio_guide_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.GettingAudioGuide],
    name="Добавить картинку в аудиогид",
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
    tags=["Административная панель / Аудиогиды"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        image: UploadFile = File(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        audio_guide_id: int = Path(..., title='Идентификатор экскурсии'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    # cache.delete_by_prefix('excursion_by_user')
    audio_guide = crud.audio_guide.get_by_id(db=db, id=audio_guide_id)
    if audio_guide is None:
        raise UnfoundEntity(num=1, message='Аудиогид не найден')

    crud.audio_guide.s3_client = s3_client
    crud.audio_guide.s3_bucket_name = s3_bucket_name
    crud.audio_guide.add_image(db=db, audio_guide=audio_guide, image=image)
    # excursion.is_accepted = None
    # db.add(excursion)
    # db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.audio_guide.get_audio_guide(audio_guide=audio_guide)
    )

@router.delete(
    '/cp/audio_guides/audios/{audio_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.GettingAudioGuide],
    name="Удалить аудиофайл аудиогида",
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
    tags=["Административная панель / Аудиогиды"]
)
def delete_audio(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        audio_id: int = Path(..., title='Идентификатор аудио'),
        # cache: Cache = Depends(deps.get_cache_list),
):
    # cache.delete_by_prefix('excursion_by_user')
    audio = crud.audio_guide.get_audio_by_id(db=db, id=audio_id)
    if audio is None:
        raise UnfoundEntity(num=1, message='Картинка не найдена')


    crud.audio_guide.s3_client = s3_client
    crud.audio_guide.s3_bucket_name = s3_bucket_name
    crud.audio_guide.delete_audio(db=db, audio=audio)
    return schemas.response.SingleEntityResponse(
        data=getters.audio_guide.get_audio_guide(audio_guide=audio.audio_guide)
    )

