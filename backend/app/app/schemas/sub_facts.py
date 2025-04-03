from typing import Optional, List

from pydantic import BaseModel

from .id_model import IdModel

class SubFactsBase(BaseModel):
    facts_name: Optional[str]

class CreatingSubFacts(SubFactsBase):
    parent_facts_id: int

class UpdatingSubFacts(SubFactsBase):
    pass

class GettingSubFacts(IdModel, BaseModel):
    id: Optional[int]
    sub_facts_name: str
    parent_facts: Optional[int]
    
class AddUserProfilSubFacts(BaseModel):
    id: List[int]

class SubFacts(BaseModel):
    sub_facts_id: int
    sub_facts_name: str
