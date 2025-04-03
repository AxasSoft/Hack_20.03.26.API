import os
import os
import uuid
from typing import Optional, Type, List

from botocore.client import BaseClient
from fastapi import UploadFile
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.base import CRUDBase
from app.getters.achievement import get_achievement
from app.models import User, UserAchievement
from app.models.achievement import Achievement
from app.schemas.achievement import CreatingAchievement, UpdatingAchievement, GettingUserAchievement
from app.utils import pagination


class CRUDAchievement(CRUDBase[Achievement, CreatingAchievement, UpdatingAchievement]):
    def __init__(self, model: Type[Achievement]):

        self.s3_bucket_name: Optional[str] = deps.get_bucket_name()
        self.s3_client: Optional[BaseClient] = deps.get_s3_client()
        super().__init__(model=model)

    def change_cover(self, db: Session, *, achievement: Achievement, new_cover: Optional[UploadFile]) -> bool:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_cover = achievement.cover

        new_url = None

        if new_cover is not None:

            name = 'achievements/covers/' + \
                uuid.uuid4().hex + os.path.splitext(new_cover.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=new_cover.file,
                ContentType=new_cover.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False

        achievement.cover = new_url
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        if old_cover is not None and old_cover.startswith(url_prefix):
            key = old_cover[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def search(
            self,
            db: Session,
            search: Optional[str] = None,
            page: Optional[int] = None,
    ):

        query = db.query(self.model)
        if search is not None:
            query = query.filter(self.model.name.ilike('%' + search + '%'))
        query = query.order_by(desc(self.model.created))

        return pagination.get_page(query=query, page=page)

    def get_user_achievements(self, db: Session, user: User) -> List[GettingUserAchievement]:

        return [
            GettingUserAchievement(
                **get_achievement(achievement=datum[0]).dict(),
                completed=datum[1]
            )
            for datum
            in db.query(self.model, UserAchievement.id != None)
            .join(
                UserAchievement,
                and_(UserAchievement.achievement_id == self.model.id, UserAchievement.user_id == user.id),
                isouter=True
            ).all()
        ]


achievement = CRUDAchievement(model=Achievement)
