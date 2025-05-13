# from botocore.client import BaseClient
# from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app import crud
from app.crud.base import CRUDBase
from app.models import ExcursionBooking, Excursion, User
from app.schemas import CreatingExcursionBooking, UpdatingExcursionBooking
from app.utils.datetime import from_unix_timestamp
from ..exceptions import UnprocessableEntity
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
        excursion = crud.excursion.get_by_id(db=db, id=excursion_id)
        group = crud.excursion_group.get_by_id(db=db, id=group_id)
        if len(members_info) >= excursion.max_group_size - group.current_members:
            raise UnprocessableEntity('Не хватает свободных мест в группе')
        db_obj = self.model(**booking_data, user_id=user_id, group_id=group_id, excursion_id=excursion_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        crud.excursion_member.create_many(db=db, data=members_info, booking_id=db_obj.id, group_id=group_id)
        return db_obj

    def update_status(self, db:Session, status: str, booking: ExcursionBooking):
        if status == ExcursionBookingStatus.REJECTED:
            members_count = 0
            for excursion_member in booking.members:
                db.delete(excursion_member)
                members_count += 1
            crud.excursion_group.update_members_count(db=db, group_id=booking.group_id, members_count=-members_count)
        booking.status = status
        db.commit()
        db.refresh(booking)
        return booking

    def get_bookings_by_user(self,
                             db: Session,
                             user: User,
                             page: Optional[int] = None
                             ):
        query = (
            db.query(ExcursionBooking).
            filter(ExcursionBooking.user_id == user.id)
        ).order_by(ExcursionBooking.created.desc())

        return pagination.get_page(query, page)


excursion_booking = CRUDExcursionBooking(ExcursionBooking)