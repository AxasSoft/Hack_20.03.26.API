# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app import crud
from app.crud.base import CRUDBase
from app.models import ExcursionBooking, Excursion
from app.schemas import CreatingExcursionBooking, UpdatingExcursionBooking
from app.utils.datetime import from_unix_timestamp
from app.utils import pagination
from app.enums.excursion_booking_status import ExcursionBookingStatus




class CRUDExcursionBooking(CRUDBase[ExcursionBooking, CreatingExcursionBooking, UpdatingExcursionBooking]):
    def create_for_user(self, db: Session,
                        *,
                        obj_in: CreatingExcursionBooking,
                        group_id: int,
                        excursion_id: int,
                        user_id: int,
                        ) -> ExcursionBooking:
        booking_data = obj_in.dict()
        members_info = booking_data.pop('members_info')
        db_obj = self.model(**booking_data, user_id=user_id, group_id=group_id, excursion_id=excursion_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        crud.excursion_member.create_many(db=db, data=members_info, booking_id=db_obj.id, group_id=group_id)
        return db_obj



excursion_booking = CRUDExcursionBooking(ExcursionBooking)