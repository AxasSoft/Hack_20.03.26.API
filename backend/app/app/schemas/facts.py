from typing import Optional, List, Dict
from .sub_facts import SubFacts
from pydantic import BaseModel, Field

from .id_model import IdModel

class FactsBase(BaseModel):
    facts_name: Optional[str]


class CreatingFacts(FactsBase):
    pass 


class UpdatingFacts(FactsBase):
    pass


class GettingFacts(IdModel, FactsBase):
    pass

class FactsSubFacts(BaseModel):
    facts_id: int
    facts_name: str
    sub_facts: List[SubFacts]