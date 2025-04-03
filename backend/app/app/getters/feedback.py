from app.getters import get_user_short_info
from app.models import Feedback
from app.schemas import GettingFeedback
from app.utils.datetime import to_unix_timestamp


def get_feedback(feedback: Feedback) -> GettingFeedback:

    if feedback.subject_id is None:
        if feedback.is_offer:
            user = feedback.offer.user
        else:
            user = feedback.offer.order.user
    else:
        user = feedback.subject

    return GettingFeedback(
        id=feedback.id,
        created=to_unix_timestamp(feedback.created),
        text=feedback.text,
        rate=feedback.rate,
        user=get_user_short_info(user)
    )
