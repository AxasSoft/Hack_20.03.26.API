from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models.hashtag import Hashtag
from app.schemas.hashtag import CreatingHashtag, UpdatingHashtag
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session


class CRUDHashtag(CRUDBase[Hashtag, CreatingHashtag, UpdatingHashtag]):

    def update(
        self,
        db: Session,
        *,
        db_obj: Hashtag,
        obj_in: Union[UpdatingHashtag, Dict[str, Any]]
    ) -> Hashtag:
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
    ) -> Tuple[List[Hashtag], Paginator]:
        hashtags = db.query(Hashtag)
        if search is not None:
            hashtags = hashtags.filter(Hashtag.text.ilike(f'%{search}%'))
        hashtags = hashtags.order_by(Hashtag.text)
        return pagination.get_page(hashtags, page)


hashtag = CRUDHashtag(Hashtag)
