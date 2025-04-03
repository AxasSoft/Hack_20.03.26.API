from typing import Any, Optional, Type, List, Tuple
from app.models import Story
from app.schemas.response import Paginator
from app.utils import pagination

from sqlalchemy import String, or_, func, desc
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import User

from ..models import StoryReport
from ..schemas.story_report import CreatingStoryReport, UpdatingStoryReport


class CRUDStoryReport(CRUDBase[StoryReport, CreatingStoryReport, UpdatingStoryReport]):

    def get_multi(
            self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[StoryReport], Paginator]:

        query = db.query(StoryReport).order_by(StoryReport.is_satisfy != None, desc(StoryReport.created))

        return pagination.get_page(query, page)

    def create_for_users(self, db: Session, *, obj_in: CreatingStoryReport,subject:User,object_:Story):
        report = StoryReport()
        report.object_ = object_
        report.subject = subject
        report.additional_text = obj_in.additional_text
        report.reason = obj_in.reason
        db.add(report)
        db.commit()
        db.refresh(report)
        return report


story_report = CRUDStoryReport(StoryReport)
