# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app import crud
from app.crud.base import CRUDBase
from app.models import RestaurantReview, Restaurant
from app.schemas import CreatingRestaurantReview, UpdatingRestaurantReview
from app.utils.datetime import from_unix_timestamp
from app.utils import pagination




class CRUDRestaurantReview(CRUDBase[RestaurantReview, CreatingRestaurantReview, UpdatingRestaurantReview]):
    def get_by_restaurant(self,
                         db: Session,
                         restaurant: Restaurant,
                         page: Optional[int] = None):
        query = db.query(RestaurantReview).filter(RestaurantReview.restaurant_id == restaurant.id).order_by(RestaurantReview.created.desc())
        return pagination.get_page(query, page)

    def create(self, db: Session, *, obj_in: CreatingRestaurantReview, user_id: int, restaurant_id: int) -> RestaurantReview:
        visit_date = from_unix_timestamp(obj_in.visit_date)
        db_obj = self.model(visit_date=visit_date,
                            description=obj_in.description,
                            rating=obj_in.rating,
                            user_id=user_id,
                            restaurant_id=restaurant_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        crud.restaurant.update_rating(db=db, restaurant_id=restaurant_id)
        return db_obj



restaurant_review = CRUDRestaurantReview(RestaurantReview)