from typing import Optional, List
import logging

from app.models import Device, User, Notification
from pyfcm import FCMNotification
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .base_consumer import BaseConsumer


class DbConsumer(BaseConsumer):

    def notify(
            self,
            db: Session,
            recipient: User,
            text: str,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            **kwargs
    ):

        notification = Notification()
        notification.user = recipient
        notification.title = title
        notification.body = text
        notification.icon = icon

        kwargs = kwargs['kwargs']

        if 'offer_id' in kwargs:
            notification.offer_id = kwargs['offer_id']
        if 'order_id' in kwargs:
            notification.order_id = kwargs['order_id']
        if 'stage' in kwargs:
            notification.stage = kwargs['stage']
        if 'link' in kwargs:
            notification.link = kwargs['link']

        db.add(notification)
        db.commit()

    def notify_many(
            self,
            db: Session,
            recipients: List[User],
            text: str,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            **kwargs
    ):
        for recipient in recipients:
            print(recipient.id)
            notification = Notification()
            notification.user = recipient
            notification.title = title
            notification.body = text
            notification.icon = icon

            if 'offer_id' in kwargs:
                notification.offer_id = kwargs['offer_id']
            if 'order_id' in kwargs:
                notification.order_id = kwargs['order_id']
            if 'stage' in kwargs:
                notification.stage = kwargs['stage']
            if 'link' in kwargs:
                notification.link = kwargs['link']

            db.add(notification)

        db.commit()

