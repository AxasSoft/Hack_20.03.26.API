from app.getters.restaurant_review import get_restaurant_review
from app.models import Restaurant, User, RestaurantReview
from app.schemas import GettingRestaurant, GettingImage, GettingRestaurantReview
from app.utils.datetime import to_unix_timestamp
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app.utils.datetime import to_unix_timestamp


def get_restaurant(db: Session, restaurant: Restaurant) -> GettingRestaurant:
    data = {c.key: getattr(restaurant, c.key) for c in inspect(restaurant).mapper.column_attrs}
    reviews = db.query(RestaurantReview).filter(RestaurantReview.restaurant_id == restaurant.id).order_by(RestaurantReview.created.desc()).limit(5).all()
    result = GettingRestaurant(
        **data,
        phone_numbers = [
            number.phone_number for number in restaurant.phone_numbers
        ],
        images = [
            image.image
            for image in restaurant.images
        ],
        reviews = [
            GettingRestaurantReview(
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
            for restaurant_review in reviews
        ]
    )
    return result