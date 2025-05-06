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
    response_model=schemas.SingleEntityResponse,
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
    crud.transfer.create(db, obj_in=data, user_id=current_user.id)
    crud.transfer.send_email(data=data, user=current_user)
    return schemas.SingleEntityResponse(
        message="Ok"
    )


@router.get(
    '/cp/transfers/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingTransfer],
    name="Список трансферов",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Административная панель / Трансфер"]
)
def get_all(
        page: Optional[int] = Query(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    data, paginator = crud.transfer.get_page(
        db=db,
        page=page
    )
    return schemas.response.ListOfEntityResponse(
        data=[
            getters.transfer.get_transfer(transfer=transfer)
            for transfer
            in data
        ],
        meta=schemas.response.Meta(paginator=paginator)
    )


#     email_sender = SmtpEmailSender()
#     email_body = f"""
# <h3>Заявка на трансфер от:</h3>
# <h3>{current_user.first_name if current_user.first_name else ''}
# {current_user.patronymic if current_user.patronymic else ''}
# {current_user.last_name if current_user.last_name else ''}</h3>
# <h3>Телефон: {current_user.tel if current_user.tel else ''}</h3><br>
# <h3>Тип машины: {data.type.description }</h3>
# <h3>Количество пассажиров: {data.passengers_quantity}</h3>
# """
#     if data.child_seat:
#         email_body += "<h3>Необходимо детское кресло</h3>"
#     if data.animal:
#         email_body += "<h3>Необходим провоз животных</h3>"
#     if data.ski_supplies:
#         email_body += "<h3>Необходим провоз горнолыжного снаряжения</h3>"
#     if data.comment:
#         email_body += f"<h3>Комментарий: {data.comment}</h3>"
#     send_result = email_sender.send_email(
#         "Заявка на трансфер",
#         email_body
#     )
#
    # return schemas.SingleEntityResponse(
    #     message="Ok"
    # )


