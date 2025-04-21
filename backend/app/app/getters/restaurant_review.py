from app.models import RestaurantReview
from app.schemas import GettingRestaurantReview
from app.utils.datetime import to_unix_timestamp


def get_restaurant_review(restaurant_review: RestaurantReview) -> GettingRestaurantReview:
    return GettingRestaurantReview(
        id=restaurant_review.id,
        created=to_unix_timestamp(restaurant_review.created),
        updated_at=to_unix_timestamp(restaurant_review.updated_at),
        visit_date=to_unix_timestamp(restaurant_review.visit_date),
        description=restaurant_review.description,
        rating=restaurant_review.rating,
        user_id=restaurant_review.user_id,
        first_name=restaurant_review.user.first_name,
        patronymic=restaurant_review.user.patronymic,
        last_name=restaurant_review.user.last_name,
        avatar=restaurant_review.user.avatar
    )