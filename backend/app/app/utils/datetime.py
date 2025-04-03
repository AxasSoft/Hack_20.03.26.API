import datetime
import logging
from typing import Optional
import pytz


def to_unix_timestamp(dt: Optional[datetime.datetime]) -> Optional[int]:
    if dt is None:
        return None
    return int(dt.timestamp())


def from_unix_timestamp(stamp: Optional[int]):

    if stamp is None:
        return None

    return datetime.datetime.fromtimestamp(stamp)


def humanize_last_visited(dt: Optional[datetime.datetime]):
    if dt is None:
        return None
    now = datetime.datetime.utcnow()
    delta = now - dt
    delta_seconds = delta.total_seconds()
    if delta_seconds < 300:
        return 'в сети'
    elif delta_seconds < 3600:
        postfix = ''
        num = int(delta_seconds // 60)
        if 5 <=num <= 20:
            postfix = ''
        elif num % 10 == 1:
            postfix = 'у'
        elif num % 10 in (2,3,4):
            postfix = 'ы'
        return f'{num} минут{postfix} назад'
    elif delta_seconds < 86400:
        postfix = 'ов'
        num = int(delta_seconds // 3600)
        if 5 <= num <= 20:
            postfix = 'ов'
        elif num % 10 == 1:
            postfix = ''
        elif num % 10 in (2, 3, 4):
            postfix = 'а'
        return f'{num} час{postfix} назад'
    elif delta_seconds < 172800:
        return f'вчера'
    elif delta_seconds < 604800:
        postfix = 'дней'
        num = int(delta_seconds // 86400)
        if 5 <= num <= 20:
            postfix = 'дней'
        elif num % 10 == 1:
            postfix = 'день'
        elif num % 10 in (2, 3, 4):
            postfix = 'дня'
        return f'{num} {postfix} назад'
    elif dt.year == now.year:
        return dt.strftime('%d.%m')
    else:
        return dt.strftime('%d.%m.%y')