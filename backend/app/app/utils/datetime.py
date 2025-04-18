import logging
from typing import Optional
import pytz
from datetime import date, datetime, time, timezone
from typing import Any


def adapt_datetime(obj: Any) -> datetime:
    if isinstance(obj, datetime):
        dt = obj
    elif isinstance(obj, time):
        dt = datetime(
            year=0,
            month=0,
            day=0,
            hour=obj.hour,
            minute=obj.minute,
            second=obj.second,
            tzinfo=obj.tzinfo,
        )
    elif isinstance(obj, date):
        dt = datetime(
            year=obj.year, month=obj.month, day=obj.day, hour=0, minute=0, second=0
        )
    else:
        dt = datetime(
            year=getattr(obj, "year", 0),
            month=getattr(obj, "month", 0),
            day=getattr(obj, "day", 0),
            hour=getattr(obj, "hour", 0),
            minute=getattr(obj, "minute", 0),
            second=getattr(obj, "second", 0),
            tzinfo=getattr(obj, "tzinfo", None),
        )
    return dt

def to_unix_timestamp(dt: Any) -> Optional[int]:
    if dt is None:
        return None
    dt = adapt_datetime(dt)
    # return int(dt.timestamp())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    else:
        dt = dt.astimezone(timezone.utc)

    return int(dt.timestamp())



def from_unix_timestamp(stamp: Optional[int]):

    if stamp is None:
        return None

    return datetime.fromtimestamp(stamp)


def humanize_last_visited(dt: Optional[datetime]):
    if dt is None:
        return None
    now = datetime.utcnow()
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