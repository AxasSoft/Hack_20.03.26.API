import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional, Union, Type, List, Tuple
import os

from fastapi.encoders import jsonable_encoder

from app.models import Info, User
from app.schemas import Paginator
from app.utils import pagination
from botocore.client import BaseClient

from fastapi import UploadFile
from fastapi.params import File
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import func, and_, desc, or_, not_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase, ModelType
from app.models.info import Info
from app.models.story import Story
from app.schemas.info import CreatingInfo, UpdatingInfo


class CRUDInfo(CRUDBase[Info, CreatingInfo, UpdatingInfo]):

    def __init__(self, model: Type[Info]):
        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def change_image(self, db: Session, *, info: Info, new_image: Optional[UploadFile]) -> bool:

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
        logging.info(info.image)
        if old_image is not None and old_image.startswith(url_prefix):
            key = old_image[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def get_multi(
        self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[Info], Paginator]:
        return pagination.get_page(db.query(self.model).order_by(desc(self.model.important), self.model.id), page)


    def search(
            self, db: Session, *, page: Optional[int] = None, search: Optional[str] = None, category: Optional[int] = None, include_hidden: Optional[bool] = None
    ) -> Tuple[List[Info], Paginator]:



        query = db.query(self.model)

        if category is not None:
            query = query.filter(self.model.category == category)
        if search is not None:
            query = query.filter(or_(self.model.title.ilike(f'%{search}%'), self.model.body.ilike(f'%{search}%')))

        if not include_hidden:
            query = query.filter(self.model.is_hidden == False)



        query = query.order_by(desc(self.model.important), desc(self.model.created))

        return pagination.get_page(query, page)

    def get_digest(self, db: Session, *, page: Optional[int] = None) -> Tuple[List[Info], Paginator]:

        query = db.query(self.model).filter(not_(self.model.is_hidden)).order_by(self.model.category, desc(self.model.created)).distinct(self.model.category)
        return pagination.get_page(query, page)


    def create_for_user(self, db: Session, *, obj_in: CreatingInfo, user: User) -> Info:
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data['is_hidden'] = obj_in_data.get('is_hidden') == True
        db_obj = self.model(**obj_in_data, user=user)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

info = CRUDInfo(Info)

