from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models import Interests, User
from app.schemas import CreatingInterest, UpdatingInterest, InterestsSubinterests
from app.schemas.interest_dating import CreatingInterest, UpdatingInterest
from app.schemas.sub_interest import Subinterest
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

class CRUDInterests(CRUDBase[Interests, CreatingInterest, UpdatingInterest]):
        
    def update(
            self,
            db: Session,
            *,
            db_obj: Interests,
            obj_in: Union[UpdatingInterest, Dict[str, Any]],
            **kwargs
    ) -> Interests:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return super().update(db,db_obj=db_obj,obj_in=update_data)

    # def search(
    #         self,
    #         db: Session,
    #         *,
    #         search: Optional[str],
    #         page: Optional[int] = None
    # ) -> Tuple[List[Interests], Paginator]:
    #     interests = db.query(self.model)
    #     if search is not None:
    #         interests = interests.filter(self.model.name.ilike(f'%{search}%'))
    #     interests = interests.order_by(self.model.name)
    #     return pagination.get_page(interests, page)
    


    def get_interests(self, db: Session, page: int = None, page_size: int = None):
        query = db.query(Interests).filter(Interests.parent_interest_id == None)
        
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        
        sub_interests = query.all()
        total = query.count()
        
        return sub_interests, total


    def get_all_interests_subinterests(self, db: Session) -> List[InterestsSubinterests]:
        interests = db.query(Interests).filter(Interests.parent_interest_id == None).options(joinedload(Interests.subinterests)).all()
        
        result = []

        for interest in interests:
        
            subinterests = []  
            if interest.parent_interest is not None:
                for subinterest in interest.parent_interest:
                    subinterests.append(Subinterest(
                    subinterest_id=subinterest.id,
                    subinterest_name=subinterest.interest_name
                ))
            else:
                subinterests = []
            interest_subinterests = InterestsSubinterests(
                interest_id=interest.id,
                interest_name=interest.interest_name,
                subinterests=subinterests
            )
            result.append(interest_subinterests)
            
        return result
    


interests = CRUDInterests(Interests)