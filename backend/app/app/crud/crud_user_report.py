from typing import Optional, List, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import User
from app.models.user_report import UserReport
from app.schemas.response import Paginator
from app.schemas.user_report import CreatingUserReport, UpdatingUserReport
from app.utils import pagination


class CRUDUserReport(CRUDBase[UserReport, CreatingUserReport, UpdatingUserReport]):

    def get_multi(
            self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[UserReport], Paginator]:

        query = db.query(UserReport).order_by(UserReport.is_satisfy != None, desc(UserReport.created))

        return pagination.get_page(query, page)

    def create_for_users(self, db: Session, *, obj_in: CreatingUserReport,subject:User,object_:User):
        report = UserReport()
        report.object_ = object_
        report.subject = subject
        report.additional_text = obj_in.additional_text
        report.reason = obj_in.reason
        db.add(report)
        db.commit()
        db.refresh(report)
        return report


user_report = CRUDUserReport(UserReport)
