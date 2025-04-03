from abc import abstractmethod, ABC
from typing import Optional, List

from sqlalchemy.orm import Session

from ...models import User


class BaseConsumer(ABC):

    @abstractmethod
    def notify(
            self,
            db: Session,
            recipient: User,
            text: str, title: Optional[str] = None,
            icon: Optional[str] = None,
            **kwargs
    ):
        pass


    @abstractmethod
    def notify_many(
            self,
            db: Session,
            recipients: List[User],
            text: str, title: Optional[str] = None,
            icon: Optional[str] = None,
            **kwargs
    ):
        pass
