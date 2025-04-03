from typing import Optional
import os

import logging
from app.crud.base import CRUDBase
from botocore.client import BaseClient
from fastapi import UploadFile

from ..models import Page
from ..schemas import CreatingPage, UpdatingPage


class CRUDPage(CRUDBase[Page, CreatingPage, UpdatingPage]):
    def upload_pdf(self, slug: str, file: UploadFile, s3_bucket_name: str, s3_client: BaseClient):
        host = s3_client._endpoint.host

        bucket_name = s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'documents/'+slug

        new_url = url_prefix + name

        result = s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=file.file,
            ContentType=file.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return False



page = CRUDPage(Page)
