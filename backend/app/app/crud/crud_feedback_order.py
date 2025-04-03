from app.crud.base import CRUDBase
from app.models.feedback_order import FeedbackOrder
from app.schemas.feedback_order import CreatingFeedbackOrder, UpdatingFeedbackOrder
import logging
from typing import Optional, Tuple, List, Union, Dict, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, desc, alias, func, and_, not_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Order, Feedback
from app.models.offer import Offer
from app.models.order import Stage
from app.exceptions import UnfoundEntity
from app.models.user import User
from app.schemas import Paginator
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp

class CRUDFeedbackOrder(CRUDBase[FeedbackOrder, CreatingFeedbackOrder, UpdatingFeedbackOrder]):
    def search(
            self,
            db: Session,
            *,
            user: Optional[User] = None,
            order: Optional[Order] = None,
            page: Optional[int] = None
    ):
        owner_order = order.user

        query = db.query(FeedbackOrder).filter(
            FeedbackOrder.owner_order == owner_order,
        ).order_by(desc(FeedbackOrder.created))

        return pagination.get_page(query, page)

    def create_feedback_for_user(self, db: Session, *, obj_in: CreatingFeedbackOrder, 
                        creator: User, order: Order) -> FeedbackOrder:

        owner_order = order.user

    
        existing_feedback = db.query(FeedbackOrder).filter(
            FeedbackOrder.creator_id == creator.id,
            FeedbackOrder.order_id == order.id
        ).first()

        if existing_feedback:
            raise UnfoundEntity(num=2, message='Пользователь уже оставил отзыв для этого объявения', 
                                description='Пользователь уже оставил отзыв для этого объявения')

        
        
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, creator=creator, order=order, owner_order=owner_order)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

    
        owner_order.rating += obj_in_data.get('rate')
        owner_order.count_feedback_order += 1
        db.add(owner_order)
        db.commit()

        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Feedback,
        obj_in: Union[UpdatingFeedbackOrder, Dict[str, Any]]
    ) -> Feedback:

    
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        old_rate = db_obj.rate
        new_rate = update_data.get('rate', None)

        result = super().update(db=db,db_obj=db_obj,obj_in=update_data)
        owner_order = result.owner_order

        
        owner_order.rating -= old_rate
        owner_order.rating += new_rate
        db.add(owner_order)
        db.commit()
        
        return result
    
    def remove(self, db: Session, *, feedback: FeedbackOrder) -> None:
        owner_order = feedback.owner_order
        if owner_order.rating != 0:
            owner_order.rating -= feedback.rate
        owner_order.count_feedback_order -= 1
        db.add(owner_order)
        db.commit()

        super().remove(db=db, id=feedback.id)




feedback_order = CRUDFeedbackOrder(FeedbackOrder)