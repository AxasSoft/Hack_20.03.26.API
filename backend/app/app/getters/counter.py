from app.models import Counter
from app.schemas.counter import GettingCounter


def get_counter(db_obj: Counter) -> GettingCounter:
    return GettingCounter(
        id=db_obj.id,
        platform=db_obj.platform,
        value=db_obj.value
    )