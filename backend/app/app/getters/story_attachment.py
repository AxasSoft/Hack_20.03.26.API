from .timestamp import to_timestamp
from ..models import StoryAttachment
from ..schemas import GettingStoryAttachment


def get_story_attachment(db_obj: StoryAttachment) -> GettingStoryAttachment:
    return GettingStoryAttachment(
        id=db_obj.id,
        is_image=db_obj.is_image,
        main_link=db_obj.main_link,
        cover_link=db_obj.cover_link,
        created=to_timestamp(db_obj.created)
    )