import logging
import os.path
import uuid
from typing import Any, List, Optional

import boto3
from app.models import User
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
# from ....email_senders import BaseEmailSender

router = APIRouter()


@router.get(
    '/cp/interest/',
    tags=['Панель управления / Интересы'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingInterestUser],
    name="Получить все доступные интересы",

)
def get_all(
        db: Session = Depends(deps.get_db),
        search: Optional[str] = Query(None,title="текст интереса"),
        user: User = Depends(deps.get_current_active_superuser)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.interest_user.get_interest_user(interest)
            for interest
            in crud.interest_user.search(db=db, page=None, search=search)[0]
        ]
    )


@router.get(
    '/interest/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingInterestUser],
    name="Получить все доступные интересы",
    tags=['Мобильное приложение / Интересы'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        search: Optional[str] = Query(None,title="текст интереса")
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.interest_user.get_interest_user(interest)
            for interest
            in crud.interest_user.search(db=db, page=None, search=search)[0]
        ]
    )



@router.post(
    '/cp/interest/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInterestUser],
    name="Добавить интерес",
    description="Добавить новый интерес",
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
    tags=["Панель управления / Интересы"]
)
def create_interest(
        data: schemas.CreatingInterestUser,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    interest = crud.interest_user.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.interest_user.get_interest_user(interest)
    )


@router.put(
    '/cp/interest/{interest_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInterestUser],
    name="Изменить интерес",
    description="Изменить интерес",
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
            'description': 'Интерес не найден'
        }
    },
    tags=["Панель управления / Интересы"]
)
def edit_interest(
        data: schemas.UpdatingInterest,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        interest_id: int = Path(..., description="Идентификатор интереса")
):

    interest = crud.interest_user.get_by_id(db, interest_id)
    if interest is None:
        raise UnfoundEntity(
            message="Интерес не найден"
        )
    interest = crud.interest_user.update(db, db_obj=interest, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.interest_user.get_interest_user(interest)
    )


@router.delete(
    '/cp/interest/{interest_id}/',
    response_model=schemas.OkResponse,
    name="Удалить интерес",
    description="Удалить интерес",
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
            'description': 'Интерес не найден'
        }
    },
    tags=["Панель управления / Интересы"]
)
def delete_interest(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        interest_id: int = Path(..., description="Идентификатор интереса")
):

    interest = crud.interest_user.get_by_id(db, interest_id)
    if interest is None:
        raise UnfoundEntity(
            message="Интерес не найден"
        )

    crud.interest_user.remove(db=db, id=interest_id)

    return schemas.OkResponse()
