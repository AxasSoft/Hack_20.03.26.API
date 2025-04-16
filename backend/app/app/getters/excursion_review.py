from app.models import ExcursionReview
from app.schemas import GettingExcursionReview
from app.utils.datetime import to_unix_timestamp


def get_excursion_review(excursion_review: ExcursionReview) -> GettingExcursionReview:
    print(excursion_review)
    return GettingExcursionReview(
        id=excursion_review.id,
        created=to_unix_timestamp(excursion_review.created),
        updated_at=to_unix_timestamp(excursion_review.updated_at),
        visit_date=to_unix_timestamp(excursion_review.visit_date),
        description=excursion_review.description,
        rating=excursion_review.rating,
        user_id=excursion_review.user_id,
        first_name=excursion_review.user.first_name,
        patronymic=excursion_review.user.patronymic,
        last_name=excursion_review.user.last_name,
        avatar=excursion_review.user.avatar
    )