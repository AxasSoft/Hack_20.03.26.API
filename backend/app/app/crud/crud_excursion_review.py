# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import ExcursionReview, Excursion
from app.schemas import CreatingExcursionReview, UpdatingExcursionReview
from app.utils.datetime import from_unix_timestamp




class CRUDExcursionReview(CRUDBase[ExcursionReview, CreatingExcursionReview, UpdatingExcursionReview]):
    def get_by_excursion(self,
                        db: Session,
                        excursion: Excursion):
        reviews = db.query(ExcursionReview).order_by(ExcursionReview.created.desc()).all()
        return reviews

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
        return db_obj



excursion_review = CRUDExcursionReview(ExcursionReview)