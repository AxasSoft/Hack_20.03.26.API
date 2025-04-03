import datetime
import logging
from typing import Optional, Tuple, List, Union, Dict, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, desc, alias, func, and_, not_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase, CreateSchemaType, ModelType
from app.models import Order, Feedback, EventFeedback
from app.models.offer import Offer
from app.models.order import Stage

from app.models.user import User
from app.schemas import Paginator, CreatingFeedback, UpdatingFeedback, CreatingEventFeedback, UpdatingEventFeedback
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp


class CrudEventFeedback(CRUDBase[EventFeedback, CreatingEventFeedback, UpdatingEventFeedback]):
    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        db_obj = self.model()
        db_obj.text = obj_in.text
        db_obj.rate = obj_in.rate
        db_obj.created = datetime.datetime.utcnow()
        db_obj.user = kwargs['user']
        db_obj.event = kwargs['event']
        db.add(db_obj)
        db.commit()
        kwargs['event'].rating = (
            db.query(func.avg(EventFeedback.rate))
            .filter(EventFeedback.event_id == kwargs['event'].id)
            .scalar()
        )
        db.add(kwargs['event'])
        db.commit()

        return db_obj

    def update(
            self,
            db: Session, *,
            db_obj: ModelType,
            obj_in: Union[UpdatingEventFeedback, Dict[str, Any]],
            **kwargs
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        update_data.update(kwargs)
        db_obj.text = update_data.get('text')
        db_obj.rate = update_data.get('rate')
        db.add(db_obj)
        db.commit()
        db_obj.event.rating = db.query(func.avg(EventFeedback.rate)).filter(
            EventFeedback.event_id == db_obj.event_id).scalar()
        db.add(db_obj.event)
        db.commit()

        return db_obj

    def search(
            self,
            db: Session,
            user_id: Optional[int] = None,
            event_id: Optional[int] = None,
            page: Optional[int] = None
    ):
        query = db.query(self.model)
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)
        if event_id is not None:
            query = query.filter(self.model.event_id == event_id)
        return pagination.get_page(query, page)


event_feedback = CrudEventFeedback(EventFeedback)
