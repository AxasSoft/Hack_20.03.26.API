from app.enums.mod_status import ModStatus

import datetime
import time

import requests
from fastapi_utils.tasks import repeat_every
from sqlalchemy import func, extract

from app.api import deps
from app.main import app
from app.models import User, Order, Event
from app.utils.ru_unit import ru_unit
import datetime

DELTA_SECONDS = 60*60*24


@app.on_event("startup")
@repeat_every(seconds=DELTA_SECONDS, wait_first=True)
def archive_order() -> None:
    print('checking archiving order...')
    db = next(deps.get_db())
    now = datetime.datetime.utcnow().date()

    for item in db.query(Order).filter(
            Order.deadline != None,
            Order.deadline < now,
            Order.status != ModStatus.archived
    ):

        item.status = ModStatus.archived
        db.add(item)
    db.commit()


@app.on_event("startup")
@repeat_every(seconds=DELTA_SECONDS, wait_first=True)
def archive_event() -> None:
    print('checking archiving event...')
    db = next(deps.get_db())
    now = datetime.datetime.utcnow().date()

    for item in db.query(Event).filter(
            Event.ended != None,
            Event.ended < now,
            Event.status != ModStatus.archived
    ):

        item.status = ModStatus.archived
        db.add(item)
    db.commit()


