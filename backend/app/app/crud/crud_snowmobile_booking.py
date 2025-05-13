from typing import Optional, Union, Dict, Any, Type
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import text, alias, func, or_, and_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import SnowmobileBooking, User
from app.schemas import CreatingSnowmobileBooking
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp
from app.services.email_sender import SmtpEmailSender




class CRUDSnowmobileBooking(CRUDBase[SnowmobileBooking, CreatingSnowmobileBooking, CreatingSnowmobileBooking]):
    def send_email(self, data: CreatingSnowmobileBooking, user: User):
        email_sender = SmtpEmailSender()
        email_body = f"""
<h3>Заявка на бронирование снегохода от:</h3>
<h3>{user.first_name if user.first_name else ''} 
{user.patronymic if user.patronymic else ''} 
{user.last_name if user.last_name else ''}</h3>
<h3>Телефон: {user.tel if user.tel else ''}</h3><br>
<h3>Начало бронирования: {from_unix_timestamp(data.started)}</h3>
<h3>Окончание бронирования: {from_unix_timestamp(data.ended)}</h3>
<h3>Количество снегоходов: {data.snowmobile_quantity}</h3>
"""
        if data.comment:
            email_body += f"<h3>Комментарий: {data.comment}</h3>"
        send_result = email_sender.send_email(
            "Заявка на бронирование снегохода",
            email_body
        )

    def create(self, db: Session, *, obj_in: CreatingSnowmobileBooking, user_id: int) -> SnowmobileBooking:
        started = from_unix_timestamp(obj_in.started)
        ended = from_unix_timestamp(obj_in.ended)
        db_obj = self.model(started=started,
                            ended=ended,
                            user_id=user_id,
                            comment=obj_in.comment,
                            snowmobile_quantity=obj_in.snowmobile_quantity)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

snowmobile_booking = CRUDSnowmobileBooking(SnowmobileBooking)