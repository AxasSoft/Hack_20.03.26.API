# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app import crud
from app.crud.base import CRUDBase
from app.models import ExcursionGroup, Excursion
from app.schemas import CreatingExcursionGroup, UpdatingExcursionGroup
from app.utils.datetime import from_unix_timestamp
from app.utils import pagination
from app.enums.group_status import GroupStatus




class CRUDExcursionGroup(CRUDBase[ExcursionGroup, CreatingExcursionGroup, UpdatingExcursionGroup]):
    def get_by_excursion(self,
                         db: Session,
                         excursion: Excursion,
                         page: Optional[int] = None):
        query = (db.query(ExcursionGroup).
                 filter(ExcursionGroup.excursion_id == excursion.id).
                 filter(ExcursionGroup.status != GroupStatus.FINISHED).
                 order_by(ExcursionGroup.started.desc()))
        return pagination.get_page(query, page)

    def create(self, db: Session, *, obj_in: CreatingExcursionGroup, excursion_id: int) -> ExcursionGroup:
        started = from_unix_timestamp(obj_in.started)
        ended = from_unix_timestamp(obj_in.ended)
        db_obj = self.model(started=started,
                            ended=ended,
                            excursion_id=excursion_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj



excursion_group = CRUDExcursionGroup(ExcursionGroup)