from typing import Optional

from sqlalchemy.orm import Session

from app.getters import get_user, get_category, get_subcategory, get_user_short_info
from app.models import Order, User, Offer
from app.schemas import GettingOrder, GettingOrderWithWinner, GettingOffer, GettingImage
from app.utils.datetime import to_unix_timestamp

def get_order(db: Session, order: Order, current_user: Optional[User]) -> GettingOrder:

    subcategory = order.subcategory
    if subcategory is not None:
        category = subcategory.category
    else:
        category = None

    if current_user is not None:
        is_favorite = any(fo.user == current_user for fo in order.favorite_orders)
    else:
        is_favorite = None


    return GettingOrder(
        id=order.id,
        title=order.title,
        body=order.body,
        deadline=to_unix_timestamp(order.deadline),
        created=to_unix_timestamp(order.created),
        profit=order.profit,
        stage=order.stage,
        user=get_user(db=db, db_obj=order.user, db_user=current_user),
        category=get_category(category) if category is not None else None,
        subcategory=get_subcategory(subcategory) if subcategory is not None else None,
        is_block=order.is_block if order.is_block is not None else False,
        type=order.type,
        address=order.address,
        block_comment=order.block_comment,
        is_auto_recreate=order.is_auto_recreate,
        lat=order.lat,
        lon=order.lon,
        is_favorite=is_favorite,
        images=[GettingImage(id=image.id,link=image.image) for image in sorted(order.images, key=lambda x: x.id)],
        status=order.status,
        moderation_comment=order.moderation_comment,
        is_stopping=order.is_stopping,
        count_favorite=len(order.favorite_orders),
        views_counter=order.views_counter,
    )


def get_offer(db: Session, offer: Offer, current_user: Optional[User]) -> GettingOffer:
    return GettingOffer(
        id=offer.id,
        created=to_unix_timestamp(offer.created),
        user=get_user_short_info(db_obj=offer.user),
        order_id=offer.order_id,
        order=get_order(db=db,order=offer.order, current_user=current_user),
        is_winner=offer.is_winner,
        text=offer.text
    )


def get_order_with_winner(db: Session, order: Order, current_user: Optional[User]) -> GettingOrderWithWinner:

    win_offer = db.query(Offer).filter(Offer.is_winner, Offer.order_id == order.id).first()

    subcategory = order.subcategory
    if subcategory is not None:
        category = subcategory.category
    else:
        category = None
    if current_user is not None:
        is_favorite = any(fo.user == current_user for fo in order.favorite_orders)
    else:
        is_favorite = None


    result =  GettingOrderWithWinner(
        id=order.id,
        title=order.title,
        body=order.body,
        deadline=to_unix_timestamp(order.deadline),
        created=to_unix_timestamp(order.created),
        profit=order.profit,
        stage=order.stage,
        user=get_user(db=db, db_obj=order.user, db_user=current_user),
        category=get_category(category) if category is not None else None,
        subcategory=get_subcategory(subcategory) if subcategory is not None else None,
        is_block=order.is_block if order.is_block is not None else False,
        type=order.type,
        address=order.address,
        win_offer=get_offer(db=db,offer=win_offer,current_user=current_user) if win_offer is not None else None,
        block_comment=order.block_comment,
        is_auto_recreate=order.is_auto_recreate,
        images=[GettingImage(id=image.id,link=image.image) for image in sorted(order.images, key=lambda x: x.id)],
        is_favorite=is_favorite,
        lat=order.lat,
        lon=order.lon,
        status=order.status,
        moderation_comment=order.moderation_comment,
        is_stopping=order.is_stopping,
        count_favorite=len(order.favorite_orders),
        views_counter=order.views_counter,
    )

    if result.status is not None:
        result.status = result.status.value
    if result.stage is not None:
        result.stage = result.stage.value
    return result
