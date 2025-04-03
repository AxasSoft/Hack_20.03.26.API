import logging
import os.path
import uuid
from typing import Any, List, Optional
import  datetime

import boto3
from app.schemas.response import Meta, OkResponse
from botocore.client import BaseClient
from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.params import File, Path, Header, Form
from pydantic import Field
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import crud, models, schemas, getters
from app.api import deps
from app.core.config import settings
from app.utils.security import send_new_account_email
from ....exceptions import EntityError, UnprocessableEntity, UnfoundEntity, ListOfEntityError, InaccessibleEntity
# from ....email_senders import BaseEmailSender
from ....getters.event_feedback import get_event_feedback
from ....models.event_member import AcceptingStatus, EventMember
from ....notification.notificator import Notificator
from ....schemas import CreatingStory, UpdatingStory, CreatingEventFeedback, UpdatingEventFeedback
from ....schemas.story import HugBody, HidingBody
from ....utils.datetime import to_unix_timestamp

router = APIRouter()


@router.get(
    '/cp/events/{event_id}/feedbacks/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingEventFeedback],
    name="Получить отзывы о мероприятиях",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
@router.get(
    '/events/{event_id}/feedbacks/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingEventFeedback],
    name="Получить отзывы о мероприятиях",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def get_feedbacks(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(None, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        event_id: int = Path(..., title="Идентификатор мероприятия")
):
    data, paginator = crud.crud_event_feedback.event_feedback.search(db=db, page=page, event_id=event_id)

    return schemas.ListOfEntityResponse(
        meta=Meta(
            paginator=paginator
        ),
        data=[get_event_feedback(event_feedback) for event_feedback in data]
    )


@router.post(
    '/cp/events/{event_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEventFeedback],
    name="Отправить отзыв о мероприятии",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
@router.post(
    '/events/{event_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEventFeedback],
    name="Отправить отзыв о мероприятии",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def create_feedback(
        data: CreatingEventFeedback = Body(..., title="Отзыв о мероприятии"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        event_id: int = Path(..., title="Идентификатор мероприятия")
):
    event = crud.crud_event.event.get_by_id(db=db, id=event_id)
    if event is None:
        raise UnfoundEntity('Мероприятие не найдено', num=2, description="Мероприятие не найдено")
    feedback = crud.event_feedback.create(db=db, obj_in=data, event=event,user=current_user)
    return schemas.SingleEntityResponse(data=get_event_feedback(feedback))


@router.put(
    '/cp/events/feedbacks/{feedback_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEventFeedback],
    name="Изменить отзыв о мероприятии",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
@router.put(
    '/events/feedbacks/{feedback_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingEventFeedback],
    name="Изменить отзыв о мероприятии",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def edit_feedback(
        data: UpdatingEventFeedback = Body(..., title="Отзыв о мероприятии"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        feedback_id: int = Path(..., title="Идентификатор отзыва")
):
    feedback = crud.event_feedback.get_by_id(db=db, id=feedback_id)
    if feedback is None:
        raise UnfoundEntity('Отзыв не найден', num=1, description="Отзыв не найден")
    feedback = crud.event_feedback.update(db=db, db_obj=feedback, obj_in=data)
    return schemas.SingleEntityResponse(data=get_event_feedback(feedback))


@router.delete(
    '/cp/events/feedbacks/{feedback_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отзыв о мероприятии",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Мероприятия"]
)
@router.delete(
    '/events/feedbacks/{feedback_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отзыв о мероприятиии",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Мероприятия"]
)
def delete_feedback(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        feedback_id: int = Path(..., title="Идентификатор отзыва")
):
    feedback = crud.event_feedback.get_by_id(db=db, id=feedback_id)
    if feedback is None:
        raise UnfoundEntity('Отзыв не найден', num=1, description="Отзыв не найден")
    feedback = crud.event_feedback.remove(db=db, id=feedback_id)
    return schemas.OkResponse()
