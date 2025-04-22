# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List

from app import crud
from app.crud.base import CRUDBase
from app.models import ExcursionMember
from app.schemas import CreatingExcursionMember, UpdatingExcursionMember
from app.utils.datetime import from_unix_timestamp
from app.utils import pagination




class CRUDExcursionMember(CRUDBase[ExcursionMember, CreatingExcursionMember, UpdatingExcursionMember]):
    def create_many(self, db: Session,
                        *,
                        data: List[CreatingExcursionMember],
                        booking_id: int,
                        group_id: int,
                        ) -> List[ExcursionMember]:
        members = []
        members_count = 0
        for member_data in data:
            db_obj = self.model(**member_data, booking_id=booking_id, excursion_group_id=group_id)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            members.append(db_obj)
            members_count += 1
        crud.excursion_group.update_members_count(db=db, group_id=group_id, members_count=members_count)

        return members



excursion_member = CRUDExcursionMember(ExcursionMember)