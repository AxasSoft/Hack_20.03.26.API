from typing import Optional

from app.models import User
from sqlalchemy import not_
from sqlalchemy.orm import Session

from . import get_hashtag, get_user_short_admin_info, get_story_attachment
from .timestamp import to_timestamp
from ..models import Story, StoryAttachment, UserReport
from ..models.view import View
from ..models.hug import Hug
from ..schemas import GettingUserReport


def get_user_report(db: Session, db_obj: UserReport) -> GettingUserReport:

    return GettingUserReport(
        id=db_obj.id,
        created=to_timestamp(db_obj.created),
        subject=get_user_short_admin_info(db_obj.subject) if db_obj.subject is not None else None,
        object=get_user_short_admin_info(db_obj.object_) if db_obj.object_ is not None else None,
        reason=db_obj.reason,
        additional_text=db_obj.additional_text,
        is_satisfy=db_obj.is_satisfy
    )
