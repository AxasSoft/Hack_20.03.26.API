from sqlalchemy import or_, and_, not_
from sqlalchemy.orm import Session

from app.getters import get_user
from app.models import Notification, Feedback, Offer, Order
from app.schemas import GettingNotification
from app.utils.datetime import to_unix_timestamp


def get_notification(db: Session, notification: Notification) -> GettingNotification:
    if notification.order is not None:
        order_name = notification.order.title
    else:
        order_name = None

    second_user = None
    if notification.order is not None and notification.offer is not None:
        if notification.order.user_id == notification.user_id:
            second_user = notification.offer.user
        elif notification.offer.user_id == notification.user_id:
            second_user = notification.order.user

    return GettingNotification(
        id=notification.id,
        title=notification.title,
        body=notification.body,
        user=get_user(db=db, db_obj=notification.user,
                      db_user=notification.user) if notification.user is not None else None,
        created=to_unix_timestamp(notification.created),
        is_read=notification.is_read,
        stage=notification.stage,
        order_id=notification.order_id,
        offer_id=notification.offer_id,
        icon=notification.icon,
        link=notification.link,
        has_feedback_about_me=db.query(Feedback)
            .join(Offer, Feedback.offer_id == Offer.id, isouter=True)
            .join(Order, Offer.order_id == Order.id, isouter=True)
            .filter(
                notification.offer_id == Offer.id,
                Feedback.subject_id == None,
                Feedback.object_id == None,
                or_(
                    and_(Feedback.is_offer, Offer.user_id == notification.user_id),
                    and_(not_(Feedback.is_offer), Order.user_id == notification.user_id)
                )
            ).first() is not None,
        order_name=order_name,
        second_user=get_user(db=db, db_obj=second_user, db_user=notification.user) if second_user is not None else None
    )
