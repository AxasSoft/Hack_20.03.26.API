import logging
from datetime import datetime
from typing import Optional


def to_timestamp(dt: Optional[datetime],tz=None):
    if dt is None:
        return None
    dt = dt.replace(tzinfo=tz)
    result = int(dt.timestamp())
    return result

