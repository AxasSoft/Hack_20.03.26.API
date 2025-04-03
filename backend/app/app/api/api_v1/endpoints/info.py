
import logging
import os.path
import uuid
from typing import Any, List, Optional

import boto3
from app.schemas.response import Meta
from botocore.client import BaseClient
from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.params import File, Path
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.core.config import settings
from app.utils.security import send_new_account_email
from ....exceptions import EntityError, UnprocessableEntity, UnfoundEntity
import logging


from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/infos/',
    tags=['Административная панель / Информационные блоки'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingInfo],
    name="Получить все доступные информационные блоки",

)
@router.get(
    '/infos/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingInfo],
    name="Получить все доступные информационные блоки",
    tags=['Мобильное приложение / Информационные блоки'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        category: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        include_hidden: Optional[bool] = Query(False),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
        page: Optional[int] = Query(None),
        cache: Cache = Depends(deps.get_cache_list),
):
    def fatch_info():
        data, paginator = crud.info.search(db=db, category=category, search=search, page=page, include_hidden=include_hidden)
        return schemas.ListOfEntityResponse(
            data=[
                getters.info.get_info(info, db,current_user)
                for info
                in data
            ],
            meta=Meta(
                paginator=paginator
            )
        )

    key_tuple = ('info_by', f"page - {page} - include_hidden - {include_hidden} \
                 - search - {search} - category - {category}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_info, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.get(
    '/infos/digest/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingInfo],
    name="Получить информационные блоки по категории",
    tags=['Мобильное приложение / Информационные блоки'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
        page: Optional[int] = Query(None),
        cache: Cache = Depends(deps.get_cache_list),
):
    def fatch_info_digest():
        data, paginator = crud.info.get_digest(db=db, page=page)

        return schemas.ListOfEntityResponse(
            data=[
                getters.info.get_info(info, db,current_user)
                for info
                in data
            ],
            meta=Meta(
                paginator=paginator
            )
        )

    key_tuple = ('info_by', f"user_digest - {current_user.id} - page - {page}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_info_digest, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data

@router.get(
    '/infos/{info_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInfo],
    name="Получить информационный блок",
    description="Получить информационный блок",
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
            'description': 'Информационный блок не найдена'
        }
    },
    tags=["Мобильное приложение / Информационные блоки"]
)
def get_info(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_optional_current_user),
        info_id: int = Path(..., description="Идентификатор информационного блока"),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def fatch_info_id():
        info = crud.info.get_by_id(db, info_id)
        if info is None:
            raise UnfoundEntity(
                message="Информационный блок не найден"
            )

        return schemas.SingleEntityResponse(
            data=getters.info.get_info(info,db,current_user)
        )

    key_tuple = ('info_by', f"info_id - {info_id}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_info_id, ttl=7200)
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data



@router.post(
    '/cp/infos/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInfo],
    name="Добавить информационный блок",
    description="**Только для администрации**  Добавить новый информационный блок",
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
    tags=["Административная панель / Информационные блоки"]
)
def create_info(
        data: schemas.CreatingInfo,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('info_by')
    info = crud.info.create_for_user(db, obj_in=data, user=current_user)

    return schemas.SingleEntityResponse(
        data=getters.info.get_info(info,db,current_user)
    )


@router.put(
    '/cp/infos/{info_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInfo],
    name="Изменить информационный блок",
    description="**Только для администрации**  Изменить информационный блок",
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
            'description': 'Информационный блок не найдена'
        }
    },
    tags=["Административная панель / Информационные блоки"]
)
def edit_info(
        data: schemas.UpdatingInfo,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        info_id: int = Path(..., description="Идентификатор информационного блока"),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('info_by', f"info_id - {info_id}")
    cache.delete(key_tuple_user)
    info = crud.info.get_by_id(db, info_id)
    if info is None:
        raise UnfoundEntity(
            message="Информационный блок не найден"
        )
    info = crud.info.update(db, db_obj=info, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.info.get_info(info,db,current_user)
    )


@router.delete(
    '/cp/infos/{info_id}/',
    response_model=schemas.OkResponse,
    name="Удалить информационный блок",
    description="Удалить информационный блок",
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
            'description': 'Информационный блок не найден'
        }
    },
    tags=["Административная панель / Информационные блоки"]
)
def delete_info(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        info_id: int = Path(..., description="Идентификатор информационного блока"),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('info_by')
    info = crud.info.get_by_id(db, info_id)
    if info is None:
        raise UnfoundEntity(
            message="Информационный блок не найден"
        )

    crud.info.remove(db=db, id=info_id)

    return schemas.OkResponse()


@router.post(
    '/cp/infos/{info_id}/image/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInfo],
    name="Изменить изображение",
    tags=['Административная панель / Информационные блоки'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def edit_image_by_admin(
        new_image: Optional[UploadFile] = File(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        info_id: int = Path(..., title="Идентификатор полльзователя"),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('info_by')
    getting_info = crud.info.get_by_id(db, info_id)
    if getting_info is None:
        raise UnfoundEntity(message="Информационный блок не найден")

    crud.info.s3_client = s3_client
    crud.info.s3_bucket_name = s3_bucket_name

    result = crud.info.change_image(db, info=getting_info, new_image=new_image)

    if not result:
        raise UnprocessableEntity(
            message="Не удалось обновить изображение",
            description="Не удалось обновить изображение",
            num=1
        )

    return schemas.SingleEntityResponse(
        data=getters.info.get_info(getting_info,db,current_user=current_user)
    )


