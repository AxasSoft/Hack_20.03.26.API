# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import ExcursionReview, Excursion
from app.schemas import CreatingExcursionReview, UpdatingExcursionReview





class CRUDExcursionReview(CRUDBase[ExcursionReview, CreatingExcursionReview, UpdatingExcursionReview]):
    def get_by_excursion(self,
                        db: Session,
                        excursion: Excursion):
        reviews = db.query(ExcursionReview).order_by(ExcursionReview.created.desc()).all()
        return reviews



excursion_review = CRUDExcursionReview(ExcursionReview)