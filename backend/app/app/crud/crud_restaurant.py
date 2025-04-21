from typing import Optional, Union, Dict, Any, Type, List
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import Numeric, text, alias, func, or_, and_, select
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.crud.base import CRUDBase
from app.models import User, RestaurantImage
from app.models.restaurant import Restaurant
from app.models.restaurant_review import RestaurantReview
from app.schemas.restaurant import CreatingRestaurant, UpdatingRestaurant
from app.exceptions import UnprocessableEntity
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp




class CRUDRestaurant(CRUDBase[Restaurant, CreatingRestaurant, UpdatingRestaurant]):

    def __init__(self, model: Type[Restaurant]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def get_image_by_id(self, db: Session, id: Any):
        return db.query(RestaurantImage).filter(RestaurantImage.id == id).first()

    def add_image(self, db: Session, *, restaurant: Restaurant, image: UploadFile) -> Optional[RestaurantImage]:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'restaurant/images/' + uuid.uuid4().hex + os.path.splitext(image.filename)[1]

        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=image.file,
            ContentType=image.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        image = RestaurantImage()
        image.restaurant = restaurant
        image.image = new_url
        db.add(image)

        db.commit()
        db.refresh(restaurant)

        return image

    def delete_image(self, db: Session, *, image: RestaurantImage) -> None:
        db.delete(image)
        db.commit()

    def update_rating(self, db: Session, restaurant_id: int):
        restaurant = self.get_by_id(db, restaurant_id)
        stmt = select(
            func.round(
                func.cast(
                    func.avg(RestaurantReview.rating),
                    Numeric(2, 1)
                ), 1).label("avg_rating"),
                func.count(RestaurantReview.id).label("total_reviews")
        ).filter(RestaurantReview.restaurant_id == restaurant_id,
                 RestaurantReview.rating.is_not(None),
                 RestaurantReview.rating != 0
                 )
        # rate = db.scalar(stmt)
        result = db.execute(stmt).fetchone()

        restaurant.avg_rating = result.avg_rating if result.avg_rating else 0
        restaurant.total_reviews = result.total_reviews if result else 0
        db.commit()



restaurant = CRUDRestaurant(Restaurant)