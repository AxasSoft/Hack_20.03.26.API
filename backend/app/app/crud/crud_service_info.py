import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional, Union, Type, List, Tuple
import os

from app.models import Info
from app.schemas import Paginator
from app.utils import pagination
from botocore.client import BaseClient

from fastapi import UploadFile
from fastapi.params import File
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase, ModelType
from app.models.service_info import ServiceInfo
from app.models.story import Story
from app.schemas.service_info import CreatingServiceInfo, UpdatingServiceInfo


class CRUDServiceInfo(CRUDBase[ServiceInfo, CreatingServiceInfo, UpdatingServiceInfo]):

    def __init__(self, model: Type[ServiceInfo]):
        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def change_image(self, db: Session, *, info: ServiceInfo, new_image: Optional[UploadFile]) -> bool:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_image = info.image

        new_url = None

        if new_image is not None:

            name = 'infos/images/' + uuid.uuid4().hex + os.path.splitext(new_image.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=new_image.file,
                ContentType=new_image.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False

        info.image = new_url
        db.add(info)
        db.commit()
        db.refresh(info)
        if old_image is not None and old_image.startswith(url_prefix):
            key = old_image[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def get_multi(
        self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[ServiceInfo], Paginator]:
        return pagination.get_page(db.query(self.model).order_by(self.model.id), page)

    def get_by_slug(self, db: Session, slug: str):
        return db.query(self.model).filter(self.model.slug == slug).first()

service_info = CRUDServiceInfo(ServiceInfo)

