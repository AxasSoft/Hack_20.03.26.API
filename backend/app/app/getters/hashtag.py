import logging

from sqlalchemy.orm import Session

from ..models import Hashtag, Story, StoryAttachment, StoryHashtag
from ..schemas import GettingHashtag


def get_hashtag(db: Session, db_obj: Hashtag) -> GettingHashtag:

    return GettingHashtag(
        id=db_obj.id,
        text=db_obj.text,
        stories_count=db_obj.hashtag_stories.count(),
        cover=(db.query(StoryAttachment.main_link)
            .join(Story)
            .join(StoryHashtag)
            .filter(StoryHashtag.hashtag_id == db_obj.id)
            .first() or [None])[0]
    )
