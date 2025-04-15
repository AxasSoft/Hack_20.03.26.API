from app.models import ExcursionReview
from app.schemas import GettingExcursionReview


def get_excursion_review(excursion_review: ExcursionReview) -> GettingExcursionReview:
    review_data = excursion_review.__dict__
    return GettingExcursionReview(
        **review_data,
        first_name=excursion_review.user.first_name,
        patronymic=excursion_review.patronymic,
        last_name=excursion_review.last_name
    )