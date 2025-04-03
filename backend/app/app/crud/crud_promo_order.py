from typing import Optional, Type
import os
import uuid
import logging
from app.crud.base import CRUDBase
from botocore.client import BaseClient
from fastapi import UploadFile
from sqlalchemy.orm import Session
from ..models import PromoOrder
from ..schemas import CreatingPromoOrder, UpdatingPromoOrder
from app.api import deps


class CRUDPromoOrder(CRUDBase[PromoOrder, CreatingPromoOrder, UpdatingPromoOrder]):

    
    def __init__(self, model: Type[PromoOrder]):

        self.s3_bucket_name: Optional[str] = deps.get_bucket_name()
        self.s3_client: Optional[BaseClient] = deps.get_s3_client()
        super().__init__(model=model)

    def add_promo_cover(self, db: Session, *, obj: PromoOrder, image: UploadFile) -> Optional[PromoOrder]:
        

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_profile_cover = obj.cover

        new_url = None

        if image is not None:
            name = 'order/promo/' + uuid.uuid4().hex + os.path.splitext(image.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=image.file,
                ContentType=image.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return None

        obj.cover = new_url
        db.add(obj)
        db.commit()
        db.refresh(obj)
        if old_profile_cover is not None and old_profile_cover.startswith(url_prefix):
            key = old_profile_cover[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return obj



promo_order = CRUDPromoOrder(PromoOrder)