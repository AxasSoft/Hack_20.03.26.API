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

    def upload(self, db: Session, *, current_user: User, attachment: UploadFile, num:Optional[int] = None,
               is_clip: bool = False) -> Optional[StoryAttachment]:

        if 'video' not in attachment.content_type and 'image' not in attachment.content_type:
            return None

        bucket_name = self.s3_bucket_name
        host = self.s3_client._endpoint.host
        url_prefix = host + '/' + bucket_name + '/'

        short_name = uuid.uuid4().hex + os.path.splitext(attachment.filename)[1]
        name = 'stories/attachments/'+short_name
        new_url = url_prefix + name

        is_image = 'image' in attachment.content_type

        if not is_image and is_clip:
            return self.upload_streamable_video(db=db, attachment=attachment, num=num, current_user=current_user)

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

    def upload_streamable_video(
            self,
            db: Session,
            attachment: UploadFile,
            num: Optional[int],
            current_user: User
    ):
        input_body = attachment.file.read()
        try:
            # 1. Сохраняем временный файл
            temp_input = f"temp_{uuid.uuid4().hex}{os.path.splitext(attachment.filename)[1]}"
            with open(temp_input, "wb") as f:
                f.write(input_body)

            # 2. Создаем временную директорию для HLS
            output_dir = f"hls_{uuid.uuid4().hex}"
            os.makedirs(output_dir, exist_ok=True)
            hls_playlist = f"{output_dir}/playlist.m3u8"

            # 3. Конвертируем в HLS
            cmd = [
                "ffmpeg",
                "-i", temp_input,
                "-vf", "scale=-2:720",  # Масштабируем до 720p по высоте
                "-c:v", "libx264",
                "-profile:v", "main",  # Профиль H.264
                "-level", "3.1",       # Уровень H.264
                "-crf", "23",          # Качество (меньше - лучше)
                "-preset", "fast",     # Баланс между скоростью и сжатием
                "-c:a", "aac",         # Аудио кодек
                "-ar", "44100",        # Частота дискретизации аудио
                "-ac", "2",            # Стерео звук
                "-b:a", "128k",        # Битрейт аудио
                "-hls_time", "4",      # Длительность сегмента (короче для VOD)
                "-hls_playlist_type", "vod",
                "-hls_segment_filename", os.path.join(output_dir, "segment_%03d.ts"),
                "-f", "hls",
                hls_playlist
            ]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                print("FFmpeg error:", result.stderr.decode())
                return None

            # 4. Загружаем HLS файлы в S3
            hls_s3_folder = f"stories/streamable/{output_dir}/"
            playlist_url = None

            for root, _, files in os.walk(output_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_path = hls_s3_folder + file
                    with open(local_path, "rb") as f:
                        self.s3_client.put_object(
                            Bucket=self.s3_bucket_name,
                            Key=s3_path,
                            Body=f,
                            ContentType="application/vnd.apple.mpegurl" if file.endswith(".m3u8") else "video/MP2T"
                        )


            host = self.s3_client._endpoint.host
            url_prefix = host + '/' + self.s3_bucket_name + '/'

            # Генерируем обложку
            cover_link = self.generate_video_cover(temp_filename=temp_input, url_prefix=url_prefix)

            main_url = url_prefix + hls_s3_folder + "playlist.m3u8"

            # 6. Создаем запись в БД
            story_attachment = StoryAttachment(
                main_link=main_url,
                cover_link=cover_link,
                is_image=False,
                is_clip=True,
                num=num,
                user=current_user
            )

            db.add(story_attachment)
            db.commit()
            db.refresh(story_attachment)

            return story_attachment

        except Exception as e:
            logging.error(f"Error processing streamable video: {str(e)}")
            return

        finally:
            # Очистка временных файлов
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

    def generate_video_cover(
            self,
            temp_filename: str,
            url_prefix: str
    ) -> Optional[str]:
        """Генерация обложки для видео"""
        try:
            output = f"cover_{uuid.uuid4().hex}.jpeg"
            subprocess.run([
                "ffmpeg",
                "-i", temp_filename,
                "-vframes", "1",
                "-f", "image2",
                output
            ], check=True)

            with open(output, "rb") as f:
                output_body = f.read()
                output_name = f'stories/covers/{output}'
                result = self.s3_client.put_object(
                    Bucket=self.s3_bucket_name,
                    Key=output_name,
                    Body=output_body,
                    ContentType='image/jpeg'
                )
                if 200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300:
                    return url_prefix + output_name

            return None
        except Exception as e:
            logging.error(f"Error generating video cover: {str(e)}")
            return None
        finally:
            if os.path.exists(output):
                os.remove(output)
            if os.path.exists(temp_filename):
                os.remove(temp_filename)


story_attachment = CRUDStoryAttachment(StoryAttachment)