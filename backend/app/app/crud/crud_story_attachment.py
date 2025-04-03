import logging
import shutil
import subprocess
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional, Union, Type, List
import os

from botocore.client import BaseClient

from fastapi import UploadFile
from fastapi.params import File
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase, ModelType
from app.models.story_attachment import StoryAttachment
from app.models.user import User


class CRUDStoryAttachment:
    def __init__(self, model: Type[StoryAttachment]):
        self.model = model
        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None

    def upload(self, db: Session, *, current_user: User, attachment: UploadFile, num:Optional[int] = None) -> Optional[StoryAttachment]:

        if 'video' not in attachment.content_type and 'image' not in attachment.content_type:
            return None

        bucket_name = self.s3_bucket_name
        host = self.s3_client._endpoint.host
        url_prefix = host + '/' + bucket_name + '/'

        short_name = uuid.uuid4().hex + os.path.splitext(attachment.filename)[1]
        name = 'stories/attachments/'+short_name
        new_url = url_prefix + name

        input_body=attachment.file.read()

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=input_body,
            ContentType=attachment.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        cover_link = None

        is_image = 'image' in attachment.content_type

        main_link = new_url

        if not is_image:
            try:
                with open(short_name, "wb") as f:
                    f.write(input_body)
                output = uuid.uuid4().hex + ".jpeg"

                result = subprocess.run(["ffmpeg", "-i", short_name, "-vframes", "1", "-f", "image2", output, ])
                if result.returncode == 0:
                    with open(output, "rb") as f:
                        output_body = f.read()
                        output_name = 'stories/covers/'+output
                        cover_link = url_prefix+output_name
                        result = self.s3_client.put_object(
                            Bucket=bucket_name,
                            Key=output_name,
                            Body=output_body,
                            ContentType='image/jpeg'
                        )
                        if 200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300:
                            cover_link = url_prefix+output_name
                    os.remove(output)
                os.remove(short_name)
            except Exception:
                pass


        story_attachment = StoryAttachment()
        story_attachment.main_link = main_link
        story_attachment.cover_link = cover_link
        story_attachment.is_image = is_image
        story_attachment.num = num
        story_attachment.user = current_user

        db.add(story_attachment)
        db.commit()
        db.refresh(story_attachment)

        return story_attachment

    def get_by_id(self, db: Session, id: int) -> Optional[StoryAttachment]:
        return db.query(StoryAttachment).get(id)

story_attachment = CRUDStoryAttachment(StoryAttachment)