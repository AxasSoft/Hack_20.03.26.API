from datetime import timedelta
from typing import Any, Optional

import logging
from fastapi import APIRouter, Body, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils.security import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
)
from starlette.requests import Request

from ...deps import update_visit_date
from ....exceptions import EntityError, UnprocessableEntity, InaccessibleEntity
from ....getters import get_user

router = APIRouter()


@router.post(
    "/login/access-token/",
    response_model=schemas.Token,
    name="Войти с помощью email и пароля (только для интерактивной документации)",
    description=
    "Совместимый с OAuth2 метод входа. Получите токен доступа для дальнейших запросов, требующих авторизации",
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
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    x_real_ip: Optional[str] = Header(None),
    accept_language: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_firebase_token: Optional[str] = Header(None)
) -> schemas.Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db,
        email=form_data.username,
        password=form_data.password,
        host=request.client.host,
        x_real_ip=x_real_ip,
        accept_language=accept_language,
        user_agent=user_agent,
        x_firebase_token=x_firebase_token
    )
    if not user:
        raise UnprocessableEntity(
            message="Неверный логин или пароль",
            description="Неверный логин или пароль",
            num=0
        )
    elif not crud.user.is_active(user):
        raise UnprocessableEntity(
            message="Пользователь не активирован",
            description="Неверный логин или пароль",
            num=1
        )
    update_visit_date(db=db, user=user)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token=security.create_token(
        user.id,
        expires_delta=access_token_expires,
        token_type="access"
    )
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
    )


# @router.post(
#     '/recover-password/',
#     response_model=schemas.OkResponse,
#     name="Восстановить пароль",
#     description="Отправляет новый пароль на указанный email адрес",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданны невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         }
#     }
# )
# def recover_password(
#         data: schemas.EmailBody,
#         db: Session = Depends(deps.get_db),
#         sender: BaseEmailSender = Depends(deps.get_email_sender),
#         x_real_ip: Optional[str] = Header(None),
#         accept_language: Optional[str] = Header(None),
#         user_agent: Optional[str] = Header(None),
#         x_firebase_token: Optional[str] = Header(None)
# ) -> schemas.OkResponse:
#
#     crud.user.email_sender = sender
#     result = crud.user.recover_password(db=db, email=data.email)
#
#     if result == -1:
#         raise UnprocessableEntity(
#             message="Пользователь не найден"
#         )
#
#     return schemas.OkResponse()



@router.post(
    '/sign-in/',
    response_model=schemas.response.SingleEntityResponse[schemas.token.TokenWithUser],
    name="Войти по номеру телефона и коду подтверждения",
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
    tags=["Вход"]
)
def sign_in(
        request: Request,
        data: schemas.verification_code.VerifyingCode,
        db: Session = Depends(deps.get_db),
        x_real_ip: Optional[str] = Header(None),
        accept_language: Optional[str] = Header(None),
        user_agent: Optional[str] = Header(None),
        x_firebase_token: Optional[str] = Header(None)
):
    code = crud.crud_verification_code.verification_code.check_verification_code(db=db,data=data)
    if code == -3:
        raise UnprocessableEntity(message='Код не отправлялся на этот номер телефона', num=0)
    if code == -1:
        raise UnprocessableEntity(message='Код уже использован', num=1)
    if code == -2:
        raise UnprocessableEntity(message='Время жизни кода истекло', num=2)
    if code == -4:
        raise UnprocessableEntity(message='Код подтверждения не совпадает', num=2)

    user = crud.crud_user.user.create_or_get_by_tel(db=db, tel=data.tel)
    crud.crud_user.user.handle_device(
        db=db,
        owner=user,
        host=request.client.host,
        x_real_ip=x_real_ip,
        accept_language=accept_language,
        user_agent=user_agent,
        x_firebase_token=x_firebase_token
    )
    token = crud.crud_user.user.get_token(user=user)
    return schemas.response.SingleEntityResponse(
        data=schemas.token.TokenWithUser(
            user=get_user(db=db, db_obj=user,db_user=user),
            access_token=token
        )
    )


@router.post(
    '/cp/sign-in/',
    response_model=schemas.response.SingleEntityResponse[schemas.token.TokenWithUser],
    name="Войти по email и постоянному паролю",
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
    tags=["Вход"]
)
def sign_in(
        request: Request,
        data: schemas.user.EmailAndPassword,
        db: Session = Depends(deps.get_db),
        x_real_ip: Optional[str] = Header(None),
        accept_language: Optional[str] = Header(None),
        user_agent: Optional[str] = Header(None),
        x_firebase_token: Optional[str] = Header(None)
):
    user = crud.user.authenticate(
        db,
        email=data.email,
        password=data.password,
        host=request.client.host,
        x_real_ip=x_real_ip,
        accept_language=accept_language,
        user_agent=user_agent,
        x_firebase_token=x_firebase_token
    )
    if user is None:
        raise InaccessibleEntity(message='Неверный логин или пароль')

    token = crud.crud_user.user.get_token(user=user)
    return schemas.response.SingleEntityResponse(
        data=schemas.token.TokenWithUser(
            user=get_user(db=db, db_obj=user, db_user=user),
            access_token=token
        )
    )
