import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional, Union, Type, List, Tuple

from app.models import User
from app.schemas import Paginator
from app.utils import pagination
from botocore.client import BaseClient

from fastapi import UploadFile
from fastapi.params import File
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase, ModelType
from app.models.category import Category
from app.models.story import Story
from app.schemas.category import CreatingCategory, UpdatingCategory


class CRUDCategory(CRUDBase[Category, CreatingCategory, UpdatingCategory]):
    def get_multi(
        self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[Category], Paginator]:
        query = db.query(self.model).order_by(self.model.name)

        return pagination.get_page(query, page)

category = CRUDCategory(Category)

