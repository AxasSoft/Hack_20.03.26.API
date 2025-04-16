# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app import crud
from app.crud.base import CRUDBase
from app.models import ExcursionReview, Excursion
from app.schemas import CreatingExcursionReview, UpdatingExcursionReview
from app.utils.datetime import from_unix_timestamp
from app.utils import pagination




class CRUDExcursionReview(CRUDBase[ExcursionReview, CreatingExcursionReview, UpdatingExcursionReview]):
    def get_by_excursion(self,
                         db: Session,
                         excursion: Excursion,
                         page: Optional[int] = None):
        query = db.query(ExcursionReview).filter(ExcursionReview.excursion_id == excursion.id).order_by(ExcursionReview.created.desc())
        return pagination.get_page(query, page)

    def create(self, db: Session, *, obj_in: CreatingExcursionReview, user_id: int, excursion_id: int) -> ExcursionReview:
        visit_date = from_unix_timestamp(obj_in.visit_date)
        db_obj = self.model(visit_date=visit_date,
                            description=obj_in.description,
                            rating=obj_in.rating,
                            user_id=user_id,
                            excursion_id=excursion_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        crud.excursion.update_rating(db=db, excursion_id=excursion_id)
        return db_obj



excursion_review = CRUDExcursionReview(ExcursionReview)