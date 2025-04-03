import logging
from typing import Optional, List

from sqlalchemy.orm import Session

from .base_consumer import BaseConsumer
from ...models import User


class TerminalConsumer(BaseConsumer):
    def notify(
        self,
        db:Session,
        recipient: User,
        text: str,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        **kwargs
    ):
        logging.info(f'''New notification:
        
recipient: {recipient}
title: {title}
icon: {icon}
text: {text}
kwargs: {kwargs}
''')


    def notify_many(
            self,
            db:Session,
            recipients: List[User],
            text: str,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            **kwargs
    ):
        logging.info(f'''New notification:
        
recipients: {len(recipients)}
title: {title}
icon: {icon}
text: {text}
kwargs: {kwargs}
''')
