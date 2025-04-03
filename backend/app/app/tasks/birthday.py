import datetime
import time

import requests
from fastapi_utils.tasks import repeat_every
from sqlalchemy import func, extract

from app.api import deps
from app.main import app
from app.models import User
from app.utils.ru_unit import ru_unit

DELTA_SECONDS = 60*60*24


@app.on_event("startup")
@repeat_every(seconds=DELTA_SECONDS, wait_first=True)
def check_country() -> None:
    print('checking birth days...')
    db = next(deps.get_db())
    notificator = deps.get_notificator()

    now = datetime.datetime.utcnow().date()

    for user in db.query(User).filter(extract('day', User.birthtime) == now.day, extract('month', User.birthtime) == now.month):

        print(f'checking {user.tel}')
        notificator.notify(db, recipient=user, title='Поздравляем', text='Команда AXAS поздравляет вас с днём рождения', icon=None)


@app.on_event("startup")
@repeat_every(seconds=DELTA_SECONDS, wait_first=True)
def check_country() -> None:
    print('checking cake days...')
    db = next(deps.get_db())
    notificator = deps.get_notificator()

    now = datetime.datetime.utcnow().date()

    for user in db.query(User).filter(func.DATE(extract('day', User.created) == now.day, extract('month', User.created) == now.month)):

        years = now.year - user.created.year
        if years == 0:
            continue

        years_text = str(years) + ' ' + ru_unit(years, 'год', 'года', 'лет')

        print(f'checking {user.tel}')
        notificator.notify(db, recipient=user, title='Поздравляем', text=f'Вашему аккаунту {years_text}. Спасибо, что вы выбираете нас', icon=None)
