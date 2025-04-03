import os
import uuid
from typing import Optional, Type

from botocore.client import BaseClient
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.adv import Adv
from app.schemas.adv import CreatingAdv, UpdatingAdv


class CRUDAdv(CRUDBase[Adv, CreatingAdv, UpdatingAdv]):

    def __init__(self, model: Type[Adv]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def change_cover(self, db: Session, *, adv: Adv, new_cover: Optional[UploadFile]) -> bool:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_cover = adv.cover

        new_url = None

        if new_cover is not None:

            name = 'stories/covers/' + uuid.uuid4().hex + os.path.splitext(new_cover.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=new_cover.file,
                ContentType=new_cover.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False

        adv.cover = new_url
        db.add(adv)
        db.commit()
        db.refresh(adv)
        if old_cover is not None and old_cover.startswith(url_prefix):
            key = old_cover[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def remove(self, db: Session, *, id: int) -> Adv:
        db_adv: Optional[Adv] = self.get_by_id(db=db, id=id)
        if db_adv is not None:
            for slide in db_adv.slides:
                db.delete(slide)
        db.commit()
        return super().remove(db=db, id=id)


adv = CRUDAdv(Adv)
