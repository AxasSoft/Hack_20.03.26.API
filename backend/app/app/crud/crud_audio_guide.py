from typing import Optional, Union, Dict, Any, Type, List
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import Numeric, text, alias, func, or_, and_, select
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.crud.base import CRUDBase
from app import crud
from app.models import User, AudioGuideFile
from app.models.audio_guide import AudioGuide
from app.schemas.audio_guide import CreatingAudioGuide, UpdatingAudioGuide
from app.exceptions import UnprocessableEntity, UnfoundEntity
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp




class CRUDAudioGuide(CRUDBase[AudioGuide, CreatingAudioGuide, UpdatingAudioGuide]):

    def __init__(self, model: Type[AudioGuide]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def get_audio_by_guide(self, db: Session, audio_guide: AudioGuide):
        return db.query(AudioGuideFile).filter(AudioGuideFile.audio_guide_id == audio_guide.id).first()

    def get_audio_by_id(self, db: Session, id: int):
        return db.query(AudioGuideFile).filter(AudioGuideFile.id == id).first()

    def add_audio_s3(self, audio_file: UploadFile):
        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'audio_guide/audios/' + uuid.uuid4().hex + os.path.splitext(audio_file.filename)[1]

        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=audio_file.file,
            ContentType=audio_file.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        return new_url

    # def create(self, db: Session, *, obj_in: CreatingAudioGuide, audio_file: UploadFile) -> Optional[AudioGuide]:
    #
    #     audio_url = self.add_audio(audio_file=audio_file)
    #
    #     audio_guide = AudioGuide(
    #         title=obj_in.title,
    #         description=obj_in.description,
    #         lat=obj_in.lat,
    #         lon=obj_in.lon,
    #     )
    #     db.add(audio_guide)
    #     db.commit()
    #     db.refresh(audio_guide)
    #
    #     audio_file = AudioGuideFile(audio=audio_url, audio_guide=audio_guide)
    #     db.add(audio_file)
    #
    #     db.commit()
    #     db.refresh(audio_file)
    #     db.refresh(audio_guide)
    #
    #     return audio_guide

    def add_audio(self, db: Session, audio_guide: AudioGuide, audio_file: UploadFile):
        # old_audio_file = self.get_audio_by_guide(db=db, audio_guide=audio_guide)
        # db.delete(old_audio_file)
        # db.commit()

        new_audio_url = self.add_audio_s3(audio_file=audio_file)

        audio_file = AudioGuideFile(audio=new_audio_url, audio_guide=audio_guide)
        db.add(audio_file)

        db.commit()
        db.refresh(audio_file)
        db.refresh(audio_guide)

        return audio_guide

    def delete_audio(self, db: Session, *, audio: AudioGuideFile) -> None:
        db.delete(audio)
        db.commit()


audio_guide = CRUDAudioGuide(AudioGuide)