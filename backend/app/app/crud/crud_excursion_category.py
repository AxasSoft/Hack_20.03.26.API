from typing import Optional, Union, Dict, Any, Type, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
import uuid
import os

from botocore.client import BaseClient
from app.crud.base import CRUDBase
from app.models import User, AcceptingStatus, ExcursionCategoryImage, ExcursionCategory, Excursion
from app.schemas import CreatingExcursionCategory, UpdatingExcursionCategory
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp




class CRUDExcursionCategory(CRUDBase[ExcursionCategory, CreatingExcursionCategory, UpdatingExcursionCategory]):
    def __init__(self, model: Type[ExcursionCategory]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def get_image_by_id(self, db: Session, id: Any):
        return db.query(ExcursionCategoryImage).filter(ExcursionCategoryImage.id == id).first()

    def add_image(self, db: Session, *, excursion_category: ExcursionCategory, image: UploadFile) -> Optional[ExcursionCategoryImage]:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'excursion_category/images/' + uuid.uuid4().hex + os.path.splitext(image.filename)[1]

        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=image.file,
            ContentType=image.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        image = ExcursionCategoryImage()
        image.excursion_category = excursion_category
        image.image = new_url
        db.add(image)

        db.commit()
        db.refresh(excursion_category)

        return image

    def delete_image(self, db: Session, *, image: ExcursionCategoryImage) -> None:
        db.delete(image)
        db.commit()


excursion_category = CRUDExcursionCategory(ExcursionCategory)