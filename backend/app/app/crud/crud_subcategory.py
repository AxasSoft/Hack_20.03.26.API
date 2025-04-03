import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional, Union, Type, List, Tuple

from app.models import User, Category
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
from app.models.subcategory import Subcategory
from app.models.story import Story
from app.schemas.subcategory import CreatingSubcategory, UpdatingSubcategory


class CRUDSubcategory(CRUDBase[Subcategory, CreatingSubcategory, UpdatingSubcategory]):

    def get_multi(
            self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[Subcategory], Paginator]:
        query = db.query(self.model).order_by(self.model.name)
        return pagination.get_page(query, page)

    def search(self, db, *, page: Optional[int] = None, category_id: Optional[int] = None):
        query = db.query(self.model)

        if category_id is not None:
            query = query.filter(Subcategory.category_id == category_id)

        query = query.order_by(self.model.name)

        return pagination.get_page(query, page)


subcategory = CRUDSubcategory(Subcategory)


