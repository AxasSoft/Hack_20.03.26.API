from typing import Optional, Type

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.story import Story
from app.models.user import User
from app.schemas.story import CreatingStory, UpdatingStory
from ..models import Comment, UserBlock
from ..schemas import CreatingComment
from ..utils import pagination


class CRUDComment(CRUDBase[Story, CreatingStory, UpdatingStory]):

    def __init__(self, model: Type[Story]):
        super().__init__(model=model)

    def comment_story(self, db: Session, *, user: User, story: Story, obj_in: CreatingComment):
        comment = Comment()
        comment.story = story
        comment.user = user
        comment.text = obj_in.text
        db.add(comment)
        user.rating += 1
        db.add(user)
        db.commit()
        db.refresh(comment)

        return comment

    def get_story_comments(self, story: Story, page: Optional[int], current_user: Optional[User] = None):
        return pagination.get_page(
            (
                story.comments
                    .join(UserBlock, Comment.user_id == UserBlock.object_id, isouter=True)
                    .filter(UserBlock.id == None)
                    .order_by(desc(Comment.created))
            ),
            page
        )


comment = CRUDComment(Comment)
