from typing import Optional, List
import logging
from datetime import timedelta

from app.models import Device, Notification
from pyfcm import FCMNotification
from sqlalchemy import desc
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from app.core.config import settings
from .base_consumer import BaseConsumer
from ...models import User, FirebaseToken


class FireBaseConsumer(BaseConsumer):

    def __init__(self):
            self.push_service = FCMNotification(
            service_account_file=settings.fcm_service_account_file,
            project_id="mykrasnodar-a6b26",
        )

    def notify(
            self,
            db: Session,
            recipient: User,
            text: str,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            # badge: Optional[int] = None,
            **kwargs
    ):
        """
        SELECT distinct on (f.value) f.value, f.device_id, f.created, p.user_id
        FROM public.firebasetoken f
        join public.device p on f.device_id = p.id
        where p.user_id = 43 and f.created > (Now() - interval '45' day);
        """
        kwargs = {str(k): str(v) for k, v in kwargs.items()}
        for token in (
            db.query(
                FirebaseToken.value,
                FirebaseToken.device_id,
                FirebaseToken.created,
                Device.user_id,
            )
            .join(Device)
            .filter(Device.user_id == recipient.id)
            .filter(FirebaseToken.created > (func.now() - timedelta(days=45)))
            .distinct(FirebaseToken.value)
        ):
            print(token)
            print(f"Received kwargs: {kwargs}")  # Отладочный вывод
            try:
                result = self.push_service.notify(
                    fcm_token=token.value,
                    notification_title=title or "Новое уведомление",
                    notification_body=text,
                    notification_image=icon,
                    data_payload=kwargs,
                )
                print(f"PUSH-OK: {token.value:.30} | RESULT: {result}")
            except Exception:
                print(f"PUSH-FAIL: {token.value:.30}")


    def notify_many(
            self,
            db: Session,
            recipients: List[User],
            text: str,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            **kwargs
    ):

        recipients_id = [user.id for user in recipients]
        recipients_set = set()

        # badge_map = {
        #     row[0]: row[1] for row in  db.query(Notification.user_id, func.count('*'))\
        #         .filter(Notification.user_id.in_(recipients_id), not_(Notification.is_read))\
        #         .group_by(Notification.user_id)\
        #         .all()
        # }

        for token in (
            db.query(
                FirebaseToken.value,
                FirebaseToken.device_id,
                FirebaseToken.created,
                Device.user_id,
            )
            .join(Device)
            .filter(Device.user_id.in_(recipients_id))
            .filter(FirebaseToken.created > (func.now() - timedelta(days=45)))
            .distinct(FirebaseToken.value)
        ):
            try:
                result = self.push_service.notify(
                    fcm_token=token.value,
                    notification_title=title or "Новое уведомление",
                    notification_body=text,
                    notification_image=icon,
                    data_payload=kwargs,
                )
                logging.info(f"PUSH-OK: {token.value:.30} | RESULT: {result}")
                recipients_set.add(token.user_id)
            except Exception:
                logging.info(f"PUSH-FAIL: {token.value:.30}")

        logging.info(f"PUSH-many-OK: {recipients_set}")
