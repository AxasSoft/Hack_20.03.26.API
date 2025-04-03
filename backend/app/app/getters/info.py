from typing import Optional

from sqlalchemy.orm import Session

from app.getters import get_user
from app.models import Info, User
from app.schemas import GettingInfo
from app.utils.datetime import from_unix_timestamp, to_unix_timestamp


def get_info(info: Info, db:Session, current_user: Optional[User]) -> GettingInfo:
    return GettingInfo(
        id=info.id,
        created=to_unix_timestamp(info.created),
        title=info.title,
        body=info.body,
        category=info.category,
        image=info.image,
        important=info.important,
        user=get_user(db=db, db_obj=info.user, db_user=current_user) if info.user is not None and info.user.email != 'admin@example.com' else None,
        is_hidden=info.is_hidden,
        source=info.source
    )