from typing import Optional
from app.models import User
from sqlalchemy import not_
from sqlalchemy.orm import Session
from .timestamp import to_timestamp
from ..models import PromoOrder
from ..schemas import GettingPromoOrder
from app.getters.order import get_order
from app.getters.info import get_info
from app.getters.subcategory import get_subcategory


def get_promo_order(db: Session, db_obj: PromoOrder) -> GettingPromoOrder:

    return GettingPromoOrder(
        id=db_obj.id,
        created=to_timestamp(db_obj.created),
        cover=db_obj.cover,
        link=db_obj.link,
        order=get_order(db=db,order=db_obj.order,current_user=None) if db_obj.order else None,
        subcategory=get_subcategory(db_obj=db_obj.subcategory) if db_obj.subcategory else None,
        info=get_info(db=db, info=db_obj.info, current_user=None) if db_obj.info else None,
    )
