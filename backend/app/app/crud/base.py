import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.base_class import Base
from app.schemas.response import Paginator
from app.utils import pagination


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get_by_id(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).get(id)

    def get_multi(
        self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[ModelType], Paginator]:
        query = db.query(self.model)
        if hasattr(self.model, 'id'):
            query = query.order_by(self.model.id)

        return pagination.get_page(query, page)

    def get_page(
            self, db: Session, *, order_by: Optional[Any] = None, page: Optional[int] = None
    ) -> Tuple[List[ModelType], Paginator]:
        query = db.query(self.model)
        if order_by is None:
            if hasattr(self.model, 'created'):
                query = query.order_by(desc(self.model.created))
            if hasattr(self.model, 'id'):
                query = query.order_by(desc(self.model.id))
        else:
            query = query.order_by(order_by)

        return pagination.get_page(query, page)

    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, **kwargs)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        **kwargs
    ) -> ModelType:

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        update_data.update(kwargs)
        for field in dir(db_obj):
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def remove_many(self, db: Session, *, ids: List[int]):
        result = []

        for id_ in ids:
            obj = db.query(self.model).get(id_)
            if obj is not None:
                db.delete(obj)
            result.append(obj)
        db.commit()
