from typing import Optional, List, Dict
from .sub_interest import  Subinterest
from pydantic import BaseModel, Field

from .id_model import IdModel

class InterestBase(BaseModel):
    interest_name: str

class CreatingInterest(InterestBase):
    pass 


class UpdatingInterest(InterestBase):
    pass


class GettingInterest(IdModel, BaseModel):
    interest_name: str

class InterestsSubinterests(BaseModel):
    interest_id: int
    interest_name: Optional[str]
    subinterests: List[Subinterest]