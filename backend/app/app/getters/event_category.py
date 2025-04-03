from app.models import EventCategory
from app.schemas import GettingEventCategory


def get_event_category(event_category: EventCategory) -> GettingEventCategory:
    return GettingEventCategory(
        id=event_category.id,
        name=event_category.name
    )