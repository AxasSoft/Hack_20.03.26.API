import datetime
import logging
from typing import Optional, Tuple, List, Union, Dict, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, desc, alias
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Order
from app.models.offer import Offer
from app.models.order import Stage

from app.models.user import User
from app.schemas import Paginator
from app.schemas.order import CreatingOffer, UpdatingOffer
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp


class CrudOffer(CRUDBase[Offer, CreatingOffer, UpdatingOffer]):
    def search(
            self,
            db: Session,
            *,
            offer_creator: Optional[User] = None,
            order_creator: Optional[User] = None,
            order: Optional[Order] = None,
            page: Optional[int] = None
    ) -> Tuple[List[Offer], Paginator]:

        User1 = alias(User)
        User2 = alias(User)

        query = db.query(self.model).join(Order, Offer.order_id == Order.id)

        if order_creator is not None:
            query = query\
                .join(User1, Order.user_id == User1.c.id) \
                .filter(User1.c.id == order_creator.id)

        if offer_creator is not None:
            query = db.query(self.model) \
                .join(User2, Offer.user_id == User2.c.id) \
                .filter(User2.c.id == offer_creator.id)

        if order is not None:
            query = query.filter(Offer.order_id == order.id)

        query = query \
            .order_by(desc(Offer.created))

        return pagination.get_page(query, page)

    def create_for_user(self, db: Session, *, obj_in: CreatingOffer, order: Order, user: User) -> Offer:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, order=order, user=user)  # type: ignore
        user.my_offers_count += 1
        db.add(user)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def choose_winning_offer(self, db: Session, offer: Offer, is_winner: Optional[bool]):
        if not is_winner:
            for item in db.query(Offer).filter(Offer.order_id == offer.order_id):
                item.is_winner = None
                db.add(item)
            offer.order.stage = Stage.created
            db.add(offer.order)
            db.commit()
        else:

            for item in db.query(Offer).filter(Offer.order_id == offer.order_id):
                item.is_winner = item.id == offer.id
                db.add(item)

            old_order= offer.order
            old_order.stage = Stage.selected
            db.add(old_order)
            if old_order.is_auto_recreate:
                new_order = Order()
                new_order.created = datetime.datetime.utcnow()
                new_order.title = old_order.title
                new_order.body = old_order.body
                new_order.deadline = old_order.deadline
                new_order.profit = old_order.profit
                new_order.stage = Stage.created
                new_order.address = old_order.address
                new_order.type = old_order.type
                new_order.is_block = old_order.is_block
                new_order.block_comment = old_order.block_comment
                new_order.is_auto_recreate = old_order.is_auto_recreate
                new_order.subcategory_id = old_order.subcategory_id
                new_order.user_id = old_order.user_id
                db.add(new_order)
            db.commit()

        return offer

    def remove(self, db: Session, *, id: int) -> Offer:
        offer = self.get_by_id(db=db,id=id)
        if offer is not None:
            offer.user.my_offers_count -= 1
            db.add(offer.user)
            db.commit()
        return super().remove(db=db, id=id)


offer = CrudOffer(Offer)


