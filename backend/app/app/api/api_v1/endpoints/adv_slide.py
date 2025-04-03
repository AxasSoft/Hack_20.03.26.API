import datetime
from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.params import Path, File
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.exceptions import UnfoundEntity
from app.getters.adv_slide import get_adv_slide
from app.schemas.adv_slide import GettingAdvSlide

router = APIRouter()


@router.get(
    '/cp/adv-slides/',
    response_model=schemas.response.ListOfEntityResponse[schemas.adv_slide.GettingAdvSlide],
    name="Получить все слайды рекламы",
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
    tags=["Панель управления / Слайды Истории"]
)
def get_all_adv_slides(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        page: Optional[int] = Query(None),
        adv_id: Optional[int] = Query(None)
):
    data, paginator = crud.crud_adv_slide.adv_slide.search(
        db=db,
        page=page,
        adv_id=adv_id
    )
    return schemas.response.ListOfEntityResponse(
        data=[
            getters.adv_slide.get_adv_slide(adv_slide=adv_slide)
            for adv_slide
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.post(
    '/cp/adv-slides/',
    response_model=schemas.response.SingleEntityResponse[schemas.adv_slide.GettingAdvSlide],
    name="Создать слайд рекламы",
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
    tags=["Панель управления / Слайды Рекламы"]
)
def create_adv_slide(
        data: schemas.adv_slide.CreatingAdvSlide,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
):
    adv_slide = crud.crud_adv_slide.adv_slide.create(
        db=db,
        obj_in=data,
    )

    return schemas.response.SingleEntityResponse(
        data=getters.adv_slide.get_adv_slide(adv_slide=adv_slide)
    )


@router.put(
    '/cp/adv-slides/{adv_slide_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.adv_slide.GettingAdvSlide],
    name="Изменить слайд рекламы",
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
    tags=["Панель управления / Слайды Рекламы"]
)
def edit_adv_slide(
        data: schemas.adv_slide.UpdatingAdvSlide,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        adv_slide_id: int = Path(...)
):
    adv = crud.crud_adv_slide.adv_slide.get_by_id(db=db, id=adv_slide_id)

    if adv is None:
        raise UnfoundEntity(num=1, message='Реклама не найдена')

    adv_slide = crud.crud_adv_slide.adv_slide.update(
        db=db,
        db_obj=adv,
        obj_in=data
    )

    return schemas.response.SingleEntityResponse(
        data=getters.adv_slide.get_adv_slide(adv_slide=adv_slide)
    )


@router.put(
    '/cp/adv-slides/{adv_slide_id}/img/',
    response_model=schemas.response.SingleEntityResponse[GettingAdvSlide],
    name="Изменить изображения слайды рекламы",
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
    tags=["Панель управления / Слайды Рекламы"]
)
def edit_img(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        new_img: Optional[UploadFile] = File(None),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        adv_slide_id: int = Path(...)
):
    adv_slide = crud.crud_adv_slide.adv_slide.get_by_id(db=db, id=adv_slide_id)
    if adv_slide is None:
        raise UnfoundEntity(num=1, message='Слайд рекламы не найдена')

    crud.crud_adv_slide.adv_slide.s3_client = s3_client
    crud.crud_adv_slide.adv_slide.s3_bucket_name = s3_bucket_name
    crud.crud_adv_slide.adv_slide.change_img(db=db, adv_slide=adv_slide, new_img=new_img)
    return schemas.response.SingleEntityResponse(
        data=get_adv_slide(adv_slide=adv_slide)
    )


@router.delete(
    '/cp/adv-slides/{adv_slide_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.response.OkResponse],
    name="Удалить слайд рекламы",
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
    tags=["Панель управления / Слайды Рекламы"]
)
def delete_adv_slide(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        adv_slide_id: int = Path(...)
):
    adv_slide = crud.crud_adv_slide.adv_slide.get_by_id(db=db, id=adv_slide_id)

    if adv_slide is None:
        raise UnfoundEntity(num=1, message='Слайд рекламы не найдена')

    crud.crud_adv_slide.adv_slide.remove(
        db=db,
        id=adv_slide.id
    )

    return schemas.response.OkResponse()


@router.delete(
    '/cp/adv-slides/',
    response_model=schemas.response.OkResponse,
    name="Удалить несколько слайдов рекламы",
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
    tags=["Панель управления / Слайды Рекламы"]
)
def delete_adv_slides(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        ids: List[int] = Query([])
):
    crud.crud_adv_slide.adv_slide.remove_many(db=db, ids=ids)

    return schemas.response.OkResponse()
