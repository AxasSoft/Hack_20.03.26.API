from fastapi import APIRouter, Depends, UploadFile, Query
from fastapi.params import Path, File
from sqlalchemy.orm import Session
from typing import Optional

from botocore.client import BaseClient
from app import crud, models, schemas, getters
from app.api import deps
from app.services.email_sender import SmtpEmailSender
from ....exceptions import UnfoundEntity

router = APIRouter()



@router.post(
    '/transfer/',
    response_model=schemas.SingleEntityResponse[schemas.GettingExcursionCategory],
    name="Создать заявку на трансфер",
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
    tags=["Мобильное приложение / Трансфер"]
)
def transfer_request(
        data: schemas.CreatingTransferRequest,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    email_sender = SmtpEmailSender()
    email_body = f"""
<h3>Тип машины: {data.type.description }</h3>
<h3>Количество пассажиров: {data.passengers_quantity}</h3>
"""
    if data.child_seat:
        email_body += "<h3>Необходимо десткое кресло</h3>"
    if data.animal:
        email_body += "<h3>Необходим провоз животных</h3>"
    if data.ski_supplies:
        email_body += "<h3>Необходим провоз горнолыжного снаряжения</h3>"
    send_result = email_sender.send_email(
        "Заявка на трансфер",
        email_body
    )

    return schemas.SingleEntityResponse(
        message="Ok"
    )


