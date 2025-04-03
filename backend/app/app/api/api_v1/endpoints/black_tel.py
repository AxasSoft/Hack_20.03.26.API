import logging
import os.path
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, List, Optional

import boto3
from starlette.responses import StreamingResponse

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

router = APIRouter()


@router.get(
    '/cp/black-tels/export/',
    name="Экспортировать данные чёрных номеров телефона",
    tags=['Административная панель / Чёрные номера телефонов'],
)

def export(
        db: Session = Depends(deps.get_db),
):
    data = crud.black_tel.export(db)
    export_media_type = 'text/csv'

    now = datetime.utcnow().strftime('%d%m%y%H%M%S')

    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}-{dt}.csv".format(file_name='black-tels',dt=now)
    }
    return StreamingResponse(BytesIO(data), headers=export_headers, media_type=export_media_type)


@router.get(
    '/cp/black-tels/',
    tags=['Административная панель / Чёрные номера телефонов'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingBlackTel],
    name="Получить все доступные чёрные номера телефонов",

)
def get_all(
        db: Session = Depends(deps.get_db)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.black_tel.get_black_tel(black_tel)
            for black_tel
            in crud.black_tel.get_multi(db=db, page=None)[0]
        ]
    )


@router.post(
    '/cp/black-tels/',
    response_model=schemas.SingleEntityResponse[schemas.GettingBlackTel],
    name="Добавить чёрный номер телефона",
    description="Добавить новый чёрный номер телефона",
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
    tags=["Административная панель / Чёрные номера телефонов"]
)
def create_black_tel(
        data: schemas.CreatingBlackTel,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    black_tel = crud.black_tel.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.black_tel.get_black_tel(black_tel)
    )


@router.put(
    '/cp/black-tels/{black_tel_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingBlackTel],
    name="Изменить чёрный номер телефона",
    description="Изменить чёрный номер телефона",
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
            'description': 'Чёрный номер телефона не найдена'
        }
    },
    tags=["Административная панель / Чёрные номера телефонов"]
)
def edit_black_tel(
        data: schemas.UpdatingBlackTel,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        black_tel_id: int = Path(..., description="Идентификатор чёрного номера телефона")
):

    black_tel = crud.black_tel.get_by_id(db, black_tel_id)
    if black_tel is None:
        raise UnfoundEntity(
            message="Чёрный номер телефона не найден"
        )
    black_tel = crud.black_tel.update(db, db_obj=black_tel, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.black_tel.get_black_tel(black_tel)
    )


@router.delete(
    '/cp/black-tels/{black_tel_id}/',
    response_model=schemas.OkResponse,
    name="Удалить чёрный номер телефона",
    description="Удалить чёрный номер телефона",
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
            'description': 'Чёрный номер телефона не найден'
        }
    },
    tags=["Административная панель / Чёрные номера телефонов"]
)
def delete_black_tel(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        black_tel_id: int = Path(..., description="Идентификатор чёрного номера телефона")
):

    black_tel = crud.black_tel.get_by_id(db, black_tel_id)
    if black_tel is None:
        raise UnfoundEntity(
            message="Чёрный номер телефона не найден"
        )

    crud.black_tel.remove(db=db, id=black_tel_id)

    return schemas.OkResponse()