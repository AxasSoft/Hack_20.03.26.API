import datetime
from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.params import Path, File
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.exceptions import UnfoundEntity
from app.getters.adv import get_adv
from app.schemas.adv import GettingAdv

router = APIRouter()


@router.get(
    '/advs/',
    response_model=schemas.response.ListOfEntityResponse[schemas.adv.GettingAdv],
    name="Получить все рекламы",
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
    tags=["Мобильное приложение / Реклама"]
)
def get_all_advs(
        db: Session = Depends(deps.get_db),
        # current_user: models.user.User = Depends(deps.get_current_user),
        page: Optional[int] = Query(None)
):
    data, paginator = crud.crud_adv.adv.get_page(
        db=db,
        order_by=desc(models.adv.Adv.created),
        page=page
    )
    return schemas.response.ListOfEntityResponse(
        data=[
            getters.adv.get_adv(adv=adv)
            for adv
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.get(
    '/cp/advs/',
    response_model=schemas.response.ListOfEntityResponse[schemas.adv.GettingAdv],
    name="Получить все рекламы",
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
    tags=["Панель управления / Реклама"]
)
def get_all_advs(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        page: Optional[int] = Query(None)
):
    data, paginator = crud.crud_adv.adv.get_page(
        db=db,
        order_by=desc(models.adv.Adv.created),
        page=page
    )
    return schemas.response.ListOfEntityResponse(
        data=[
            getters.adv.get_adv(adv=adv)
            for adv
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.get(
    '/advs/{adv_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.adv.GettingAdv],
    name="Получить рекламу по идентификатору",
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
    tags=["Мобильное приложение / Реклама"]
)
def get_adv_id(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        adv_id: int = Path(...)
):
    adv = crud.crud_adv.adv.get_by_id(
        db=db,
        id=adv_id
    )

    if adv is None:
        raise UnfoundEntity(num=1, message='Реклама не найдена')

    return schemas.response.SingleEntityResponse(
        data=getters.adv.get_adv(adv=adv)
    )


@router.get(
    '/cp/advs/{adv_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.adv.GettingAdv],
    name="Получить рекламу по идентификатору",
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
    tags=["Панель управления / Реклама"]
)
def get_adv_id(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
        adv_id: int = Path(...)
):
    adv = crud.crud_adv.adv.get_by_id(
        db=db,
        id=adv_id
    )

    if adv is None:
        raise UnfoundEntity(num=1, message='Реклама не найдена')

    return schemas.response.SingleEntityResponse(
        data=getters.adv.get_adv(adv=adv)
    )


@router.post(
    '/cp/advs/',
    response_model=schemas.response.SingleEntityResponse[schemas.adv.GettingAdv],
    name="Создать рекламу",
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
    tags=["Панель управления / Реклама"]
)
def create_adv(
        data: schemas.adv.CreatingAdv,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
):
    adv = crud.crud_adv.adv.create(
        db=db,
        obj_in=data,
        created=datetime.datetime.utcnow()
    )

    return schemas.response.SingleEntityResponse(
        data=getters.adv.get_adv(adv=adv)
    )


@router.put(
    '/cp/advs/{adv_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.adv.GettingAdv],
    name="Изменить историю",
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
    tags=["Панель управления / Реклама"]
)
def edit_adv(
        data: schemas.adv.UpdatingAdv,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        adv_id: int = Path(...)
):
    adv = crud.crud_adv.adv.get_by_id(db=db, id=adv_id)

    if adv is None:
        raise UnfoundEntity(num=1, message='Реклама не найдена')

    adv = crud.crud_adv.adv.update(
        db=db,
        db_obj=adv,
        obj_in=data,
        created=datetime.datetime.utcnow()
    )

    return schemas.response.SingleEntityResponse(
        data=getters.adv.get_adv(adv=adv)
    )


@router.put(
    '/cp/advs/{adv_id}/cover/',
    response_model=schemas.response.SingleEntityResponse[GettingAdv],
    name="Изменить обложку рекламы",
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
    tags=["Панель управления / Реклама"]
)
def edit_cover(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        new_cover: Optional[UploadFile] = File(None),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        adv_id: int = Path(...)
):
    adv = crud.crud_adv.adv.get_by_id(db=db, id=adv_id)
    if adv is None:
        raise UnfoundEntity(num=1, message='Реклама не найдена')

    crud.crud_adv.adv.s3_client = s3_client
    crud.crud_adv.adv.s3_bucket_name = s3_bucket_name
    crud.crud_adv.adv.change_cover(db=db, adv=adv, new_cover=new_cover)
    return schemas.response.SingleEntityResponse(
        data=get_adv(adv=adv)
    )


@router.delete(
    '/cp/advs/{adv_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.response.OkResponse],
    name="Удалить рекламу",
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
    tags=["Панель управления / Реклама"]
)
def delete_adv(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        adv_id: int = Path(...)
):
    adv = crud.crud_adv.adv.get_by_id(db=db, id=adv_id)

    if adv is None:
        raise UnfoundEntity(num=1, message='реклама не найдена')

    crud.crud_adv.adv.remove(
        db=db,
        id=adv.id
    )

    return schemas.response.OkResponse()


@router.delete(
    '/cp/advs/',
    response_model=schemas.response.OkResponse,
    name="Удалить несколько реклам",
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
    tags=["Панель управления / Реклама"]
)
def delete_advs(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        ids: List[int] = Query([])
):
    crud.crud_adv.adv.remove_many(db=db, ids=ids)

    return schemas.response.OkResponse()
