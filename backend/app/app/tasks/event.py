import datetime
import time

import requests
from fastapi_utils.tasks import repeat_every

from app.api import deps
from app.main import app
from app.models import User, Event, AcceptingStatus

DELTA_SECONDS = 60

print('init events')

# @app.on_event("startup")
# @repeat_every(seconds=DELTA_SECONDS)
# def check_event() -> None:
#     print('checking events...')
#     db = next(deps.get_db())
#     notificator = deps.get_notificator()
#     now = datetime.datetime.utcnow()

#     for event in db.query(Event).filter():

#         t = 3 * 60 * 60

#         print(f'checking event {event.id}')

#         if not (t  < (event.started - now).total_seconds() < t+60):
#             print(f'event {event.id} not coming soon')
#             print(event.started - now)
#             continue



#         users = [member.user for member in event.event_members if member.status != AcceptingStatus.declined]
#         users.append(event.user)

#         print([user.tel for user in users])

#         notificator.notify_many(
#             db=db,
#             recipients=users,
#             title='У вас запланировано мероприятие',
#             text=f'Скоро начнётся мероприятие {event.name}',
#             icon=None
#         )