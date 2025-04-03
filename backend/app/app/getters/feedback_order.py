from app.getters import get_user_short_info, get_order
from app.models import FeedbackOrder
from app.schemas.feedback_order import GettingFeedbackOrder
from app.utils.datetime import to_unix_timestamp
from sqlalchemy.orm import Session


def get_feedback_order(db: Session, feedback: FeedbackOrder) -> GettingFeedbackOrder:

    # if feedback.subject_id is None:
    #     if feedback.is_offer:
    #         user = feedback.offer.user
    #     else:
    #         user = feedback.offer.order.user
    # else:
    #     user = feedback.subject

    return GettingFeedbackOrder(
        id=feedback.id,
        created=to_unix_timestamp(feedback.created),
        updated=to_unix_timestamp(feedback.updated),
        title=feedback.title,
        text=feedback.text,
        rate=feedback.rate,
        creator=get_user_short_info(feedback.creator),
        order=get_order(db=db, order=feedback.order, current_user=None),
        owner_order=get_user_short_info(feedback.owner_order),
    )
