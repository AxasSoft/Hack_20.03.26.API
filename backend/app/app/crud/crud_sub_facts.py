from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models import Facts , User, ProfileFacts
# from app.schemas import CreatingInterest, UpdatingInterest
from app.schemas.sub_facts import CreatingSubFacts, CreatingSubFacts, UpdatingSubFacts, GettingSubFacts
from app.schemas.user_interest import UserInterestSchema, SubInterestSchema, InterestSchema
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


class CRUDSubInterest(CRUDBase[Facts, CreatingSubFacts, UpdatingSubFacts]):
        
    def update(
            self,
            db: Session,
            *,
            db_obj: Facts,
            obj_in: Union[UpdatingSubFacts, Dict[str, Any]],
            **kwargs
    ) -> Facts:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db,db_obj=db_obj,obj_in=update_data)

    def create_sub_fucts(self, db: Session, obj_in: CreatingSubFacts):
        db_obj = Facts(
            facts_name=obj_in.facts_name,
            parent_facts_id=obj_in.parent_facts_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    

    def get_sub_fucts(self,
            db: Session,
            page: int = None, 
            page_size: int = None):

        query = db.query(Facts).filter(Facts.parent_facts_id != None)
        
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        
        sub_facts = query.all()
        total = query.count()
        
        return sub_facts, total
    

    def get_sub_fucts_current_user(
            self,
            db: Session,
            user: User
    ) -> GettingSubFacts:
        query = db.query(ProfileFacts).filter(ProfileFacts.dating_profile_id == user.dating_profile.id).all()
        sub_facts = []
        for profile_facts in query:
            facts = profile_facts.facts
            sub_facts.append(facts)        
        return sub_facts


sub_facts = CRUDSubInterest(Facts)