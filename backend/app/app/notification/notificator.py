import logging
from typing import Optional, List

from sqlalchemy.orm import Session

from .consumers.base_consumer import BaseConsumer
from ..models import User


class Notificator:

    def __init__(self):
        self.consumers: List[BaseConsumer] = []

    def notify(self, db: Session, recipient: User, text: str, title: Optional[str], icon: Optional[str], **kwargs):
        for consumer in self.consumers:
            try:
                consumer.notify(db=db, recipient=recipient, text=text, title=title, icon=icon, kwargs=kwargs)
            except Exception as ex:
                logging.error(ex)

    def notify_many(self, db: Session, recipients: List[User], text: str, title: Optional[str], icon: Optional[str], **kwargs):
        for consumer in self.consumers:
            consumer.notify_many(db=db, recipients=recipients, text=text, title=title, icon=icon, **kwargs)
    
