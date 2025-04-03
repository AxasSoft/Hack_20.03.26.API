from app.getters import get_user_short_info
from app.models import EventFeedback
from app.schemas import GettingEventFeedback
from app.utils.datetime import to_unix_timestamp


def get_event_feedback(event_feedback: EventFeedback) -> GettingEventFeedback:
    return GettingEventFeedback(
        id=event_feedback.id,
        created=to_unix_timestamp(event_feedback.created),
        user=get_user_short_info(event_feedback.user),
        text=event_feedback.text,
        answer_text=event_feedback.answer_text,
        rate=event_feedback.rate
    )