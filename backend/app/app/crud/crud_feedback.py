import logging
from typing import Optional, Tuple, List, Union, Dict, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, desc, alias, func, and_, not_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Order, Feedback
from app.models.offer import Offer
from app.models.order import Stage

from app.models.user import User
from app.schemas import Paginator, CreatingFeedback, UpdatingFeedback
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp


class CrudFeedback(CRUDBase[Feedback, CreatingFeedback, UpdatingFeedback]):
    def search(
            self,
            db: Session,
            *,
            by_user: Optional[User] = None,
            about_user: Optional[User] = None,
            offer: Optional[Offer] = None,
            order: Optional[Order] = None,
            page: Optional[int] = None
    ):
        User1 = alias(User)
        User2 = alias(User)
    
        query = db.query(self.model).join(Offer,isouter=True).join(Order,isouter=True)
        
        if by_user is not None:
            query = query.join(
                User1,
                or_(
                    and_(Offer.user_id == User1.c.id, Feedback.is_offer),
                    and_(Order.user_id == User1.c.id, not_(Feedback.is_offer))
                ),
                isouter=True
            )\
                .filter(
                    or_(User1.c.id == by_user.id, and_(self.model.subject_id != None, self.model.subject_id == by_user.id))
                )
        if about_user is not None:
            query = query.join(
                User2,
                or_(
                    and_(Offer.user_id == User2.c.id, not_(Feedback.is_offer)),
                    and_(Order.user_id == User2.c.id, Feedback.is_offer)
                ),
                isouter=True
            )\
                .filter(
                    or_(User2.c.id == about_user.id, and_(self.model.object_id != None, self.model.object_id == about_user.id))
                )
        if order is not None:
            query = query.filter(Order.id == order.id)
        if offer is not None:
            query = query.filter(Offer.id == offer.id)

        query = query \
            .order_by(desc(Feedback.created))

        return pagination.get_page(query, page)

    def create_for_user(self, db: Session, *, obj_in: CreatingFeedback, user: User, offer: Offer, second_user: Optional[User] = None) -> Feedback:

        if second_user is None:
            is_offer = offer.user_id == user.id
            if is_offer:
                second_user = offer.order.user
            else:
                second_user = offer.user
            subject = None
            object_ = None
        else:
            is_offer = False
            subject = user
            object_ = second_user

        
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, offer=offer, is_offer=is_offer, subject=subject, object_=object_)  # type: ignore
        db.add(user)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        rating_row = db.query(func.avg(Feedback.rate)) \
            .join(Offer) \
            .join(Order) \
            .filter(
                Feedback.rate is not None,
                or_(
                    and_(Feedback.is_offer, Order.user_id == second_user.id),
                    and_(not_(Feedback.is_offer), Offer.user_id == second_user.id),
                    self.model.object_id == second_user.id
                )
            ).first()
        if rating_row is None:
            rating = 0
        else:
            rating = rating_row[0]
        if rating is None:
            rating = 0

        if offer is not None and offer.order is not None and offer.order.user == user:
            offer.order.stage = Stage.confirmed
            db.add(offer.order)

        second_user.rating = rating
        db.add(second_user)
        db.commit()

        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Feedback,
        obj_in: Union[UpdatingFeedback, Dict[str, Any]]
    ) -> Feedback:

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        old_rate = db_obj.rate
        new_rate = update_data.get('rate', None)

        result = super().update(db=db,db_obj=db_obj,obj_in=update_data)

        if old_rate != new_rate:

            if db_obj.subject_id is None:
                is_offer = db_obj.is_offer
                if is_offer:
                    second_user = db_obj.offer.order.user
                else:
                    second_user = db_obj.offer.user
            else:
                second_user = db_obj.subject


            rating_row = db.query(func.avg(Feedback.rate)) \
                .join(Offer) \
                .join(Order) \
                .filter(
                    Feedback.rate is not None,
                    or_(
                        and_(Feedback.is_offer, Order.user_id == second_user.id),
                        and_(not_(Feedback.is_offer), Offer.user_id == second_user.id)

                    )
            ).first()


            if rating_row is None:
                rating = 0
            else:
                rating = rating_row[0] or 0
    
            second_user.rating = rating
            db.add(second_user)
            db.commit()
            
        return result
    
    def remove(self, db: Session, *, id: int) -> Feedback:
        feedback = self.get_by_id(db=db,id=id)
        if feedback is None:
            return None
        else:
            if feedback.subject_id is None:
                is_offer = feedback.is_offer
                if is_offer:
                    second_user = feedback.offer.order.user
                else:
                    second_user = feedback.offer.user
            else:
                second_user = feedback.subject

            rating_row = db.query(func.avg(Feedback.rate)) \
                .join(Offer) \
                .join(Order) \
                .filter(
                Feedback.rate is not None,
                or_(
                    and_(Feedback.is_offer, Order.user_id == second_user.id),
                    and_(not_(Feedback.is_offer), Offer.user_id == second_user.id)

                )
            ).first()
            if rating_row is None:
                rating = 0
            else:
                rating = rating_row[0] or 0

            second_user.rating = rating
            db.add(second_user)
            db.commit()

            return super().remove(db=db,id=id)


feedback = CrudFeedback(Feedback)
