from typing import Optional, List

from pydantic import BaseModel

from .id_model import IdModel

class SubInterestBase(BaseModel):
    interest_name: Optional[str]

class CreatingSubInterest(SubInterestBase):
    parent_interest_id: int


class UpdatingSubInterest(SubInterestBase):
    pass


class GettingSubInterest(IdModel, BaseModel):
    id: Optional[int]
    subinterest_name: str
    parent_interest: Optional[int]
    

class AddUserProfilSubInterest(BaseModel):
    id: List[int]


class Subinterest(BaseModel):
    subinterest_id: int
    subinterest_name: str
