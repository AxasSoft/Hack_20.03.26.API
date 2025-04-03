from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models import Interests , User, ProfileInterests
# from app.schemas import CreatingInterest, UpdatingInterest
from app.schemas.sub_interest import CreatingSubInterest, UpdatingSubInterest, AddUserProfilSubInterest, GettingSubInterest
from app.schemas.user_interest import UserInterestSchema, SubInterestSchema, InterestSchema
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


class CRUDSubInterest(CRUDBase[Interests, CreatingSubInterest, UpdatingSubInterest]):
        
    def update(
            self,
            db: Session,
            *,
            db_obj: Interests,
            obj_in: Union[UpdatingSubInterest, Dict[str, Any]],
            **kwargs
    ) -> Interests:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db,db_obj=db_obj,obj_in=update_data)

    def create_sub_interest(self, db: Session, obj_in: CreatingSubInterest):
        db_obj = Interests(
            interest_name=obj_in.interest_name,
            parent_interest_id=obj_in.parent_interest_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    

    def get_sub_interests(self,
            db: Session,
            page: int = None, 
            page_size: int = None):

        query = db.query(Interests).filter(Interests.parent_interest_id != None)
        
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        
        sub_interests = query.all()
        total = query.count()
        
        return sub_interests, total
    

    def get_sub_interests_current_user(
            self,
            db: Session,
            user: User
    ) -> GettingSubInterest:
        query = db.query(ProfileInterests).filter(ProfileInterests.dating_profile_id == user.dating_profile.id).all()
        sub_interests = []
        for profile_interest in query:
            interest = profile_interest.interest
            sub_interests.append(interest)        
        return sub_interests


sub_interest = CRUDSubInterest(Interests)