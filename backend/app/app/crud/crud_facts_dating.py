from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models import Facts, User
from app.schemas.facts import CreatingFacts, UpdatingFacts, GettingFacts, FactsSubFacts
from app.schemas.sub_facts import SubFacts
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

class CRUDFacts(CRUDBase[Facts, CreatingFacts, UpdatingFacts]):


    def update(
            self,
            db: Session,
            *,
            db_obj: Facts,
            obj_in: Union[UpdatingFacts, Dict[str, Any]],
            **kwargs
    ) -> Facts:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return super().update(db,db_obj=db_obj,obj_in=update_data)
    

    def get_facts(self, db: Session, page: int = None, page_size: int = None):
        query = db.query(Facts).filter(Facts.parent_facts_id == None)
        
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        
        facts = query.all()
        total = query.count()
        
        return facts, total
    

    def get_all_facts_subfacts(self, db: Session) -> List[FactsSubFacts]:
        facts = db.query(Facts).filter(Facts.parent_facts_id == None).options(joinedload(Facts.sub_facts)).all()
        
        result = []

        for facts in facts:
        
            subfacts = []  
            if facts.sub_facts is not None:
                for subfact in facts.sub_facts:
                    subfacts.append(SubFacts(
                    sub_facts_id=subfact.id,
                    sub_facts_name=subfact.facts_name
                ))
            else:
                subFacts = []
            facts_subfacts = FactsSubFacts(
                facts_id=facts.id,
                facts_name=facts.facts_name,
                sub_facts=subfacts
            )
            result.append(facts_subfacts)
            
        return result
    

facts = CRUDFacts(Facts)