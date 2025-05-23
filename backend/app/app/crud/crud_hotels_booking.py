from typing import Optional, Union, Dict, Any, Type
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import text, alias, func, or_, and_
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.crud.base import CRUDBase
from app.models import HotelBooking, User
from app.schemas.hotel import CreatedBooking

from app.utils import pagination
from app.utils.datetime import from_unix_timestamp
from app.enums.hotel_booking_status import HotelBookingStatus




class CRUDHotelBooking(CRUDBase[HotelBooking, CreatedBooking, CreatedBooking]):
    def get_bookings_by_user(self,
                             db: Session,
                             user: User,
                             page: Optional[int] = None
                             ):
        query = (
            db.query(HotelBooking).
            filter(
                HotelBooking.user_id == user.id,
                HotelBooking.status != HotelBookingStatus.NEW,
            )
        ).order_by(HotelBooking.created.desc())


        return pagination.get_page(query, page)

    # def hotels_search(self, data: SimpleSearchCriteria):
    #     checkin_date = str(from_unix_timestamp(data.checkin).date())
    #     checkout_date = str(from_unix_timestamp(data.checkout).date())
    #
    #     payload = {
    #         "checkin": 1,
    #         "checkout": 1,
    #         "region_id": 965849721,
    #         "guests": [
    #             {
    #                 "adults": 2,
    #                 "children": []
    #             }
    #         ]
    #
    #     }


hotel_booking = CRUDHotelBooking(HotelBooking)