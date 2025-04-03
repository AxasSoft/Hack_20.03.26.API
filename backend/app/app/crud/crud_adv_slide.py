import os
import uuid
from typing import Optional, Type, Any

from botocore.client import BaseClient
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import AdvSlide
from app.schemas.adv_slide import CreatingAdvSlide, UpdatingAdvSlide
from app.utils import pagination


class CRUDAdvSlide(CRUDBase[AdvSlide, CreatingAdvSlide, UpdatingAdvSlide]):

    def __init__(self, model: Type[AdvSlide]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def change_img(self, db: Session, *, adv_slide: AdvSlide, new_img: Optional[UploadFile]) -> bool:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_img = adv_slide.img

        new_url = None

        if new_img is not None:

            name = 'stories/images/' + uuid.uuid4().hex + os.path.splitext(new_img.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=new_img.file,
                ContentType=new_img.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False

        adv_slide.img = new_url
        db.add(adv_slide)
        db.commit()
        db.refresh(adv_slide)
        if old_img is not None and old_img.startswith(url_prefix):
            key = old_img[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def search(
            self,
            db: Session,
            *,
            order_by: Optional[Any] = None,
            page: Optional[int] = None,
            adv_id: Optional[int] = None
    ):
        query = db.query(self.model)
        if adv_id is not None:
            query = query.filter(self.model.adv_id == adv_id)
        if order_by is None:
            query = query.order_by(self.model.adv_id, self.model.id)
        else:
            query = query.order_by(order_by)
        return pagination.get_page(query=query, page=page)


adv_slide = CRUDAdvSlide(AdvSlide)
