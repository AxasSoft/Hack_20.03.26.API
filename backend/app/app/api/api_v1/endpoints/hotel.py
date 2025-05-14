from typing import Optional, List

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form, HTTPException
from fastapi.params import File, Path
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from app.schemas.hotel import RoomGuests
from app.services.etg_ostrovok_manager.etg_ostrovok_manager import ostrovok_manager
from ....enums.mod_status import ModStatus
from ....exceptions import UnprocessableEntity, UnfoundEntity, InaccessibleEntity
from ....notification.notificator import Notificator
import logging

from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/hotels/',
    # response_model=schemas.ListOfEntityResponse[schemas.GettingExcursionGroup],
    name="Поиск отеля",
    tags=["Административная панель / Отели"]
)
@router.get(
    '/hotels/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingHotelSearchInfo],
    name="Поиск отеля",
    tags=["Мобильное приложение / Отели"]
)
def get_groups(
        page: Optional[int] = Query(None),
        # db: Session = Depends(deps.get_db),
        checkin: int = Query(..., title='Дата заезда'),
        checkout: int = Query(..., title='Дата выезда'),
        guests: str = Query(..., title="Количество гостей"),
        current_user: models.User = Depends(deps.get_current_active_user),
):
    def parse_guests_query(guests_str: str = Query(...)) -> List[RoomGuests]:
        try:
            rooms = []
            for room_str in guests_str.split("-"):
                parts = room_str.split("and")
                adults = int(parts[0])
                children = list(map(int, parts[1].split("."))) if len(parts) > 1 else None
                rooms.append(RoomGuests(adults=adults, children=children))
            return rooms
        except Exception as e:
            raise HTTPException(400, f"Invalid format. Expected 'XandY.Z-XandY.Z', got '{guests_str}'. Error: {e}")

    gest_list = parse_guests_query(guests)
    data, paginator = ostrovok_manager.get_hotels(checkin=checkin, checkout=checkout, guests=gest_list, page=page)
    return schemas.ListOfEntityResponse(
        data=data,
        meta=schemas.response.Meta(paginator=paginator)
    )

