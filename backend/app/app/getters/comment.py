from typing import Optional

from app.getters import get_user_short_info
from app.getters.timestamp import to_timestamp
from app.models import Comment, User
from sqlalchemy.orm import Session

from app.schemas import GettingComment


def get_comment(db: Session, db_obj: Comment, db_user: Optional[User]):
    return GettingComment(
        id=db_obj.id,
        text=db_obj.text,
        created=to_timestamp(db_obj.created),
        user=get_user_short_info(db_obj=db_obj.user)
    )
