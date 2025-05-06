from typing import Optional, Union, Dict, Any, Type
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import text, alias, func, or_, and_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Transfer, User
from app.schemas import CreatingTransferRequest
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp
from app.services.email_sender import SmtpEmailSender




class CRUDTransfer(CRUDBase[Transfer, CreatingTransferRequest, CreatingTransferRequest]):
    def send_email(self, data: CreatingTransferRequest, user: User):
        email_sender = SmtpEmailSender()
        email_body = f"""
<h3>Заявка на трансфер от:</h3>
<h3>{user.first_name if user.first_name else ''} 
{user.patronymic if user.patronymic else ''} 
{user.last_name if user.last_name else ''}</h3>
<h3>Телефон: {user.tel if user.tel else ''}</h3><br>
<h3>Тип машины: {data.type.description}</h3>
<h3>Количество пассажиров: {data.passengers_quantity}</h3>
"""
        if data.child_seat:
            email_body += "<h3>Необходимо детское кресло</h3>"
        if data.animal:
            email_body += "<h3>Необходим провоз животных</h3>"
        if data.ski_supplies:
            email_body += "<h3>Необходим провоз горнолыжного снаряжения</h3>"
        if data.comment:
            email_body += f"<h3>Комментарий: {data.comment}</h3>"
        send_result = email_sender.send_email(
            "Заявка на трансфер",
            email_body
        )

transfer = CRUDTransfer(Transfer)