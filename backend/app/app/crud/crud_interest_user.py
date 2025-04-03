from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models.interest_user import Interest
from app.schemas.interest_user import CreatingInterestUser, UpdatingInterestUser
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session


class CRUDInterestUser(CRUDBase[Interest, CreatingInterestUser, UpdatingInterestUser]):

    def update(
            self,
            db: Session,
            *,
            db_obj: Interest,
            obj_in: Union[UpdatingInterestUser, Dict[str, Any]],
            **kwargs
    ) -> Interest:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return super().update(db,db_obj=db_obj,obj_in=update_data)

    def search(
            self,
            db: Session,
            *,
            search: Optional[str],
            page: Optional[int] = None
    ) -> Tuple[List[Interest], Paginator]:
        interests = db.query(self.model)
        if search is not None:
            interests = interests.filter(self.model.name.ilike(f'%{search}%'))
        interests = interests.order_by(self.model.name)
        return pagination.get_page(interests, page)


interest_user = CRUDInterestUser(Interest)