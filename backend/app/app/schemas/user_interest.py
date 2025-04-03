from pydantic import BaseModel
from typing import Optional

class InterestSchema(BaseModel):
    id: int
    name: str

class SubInterestSchema(BaseModel):
    id: int
    name: str
    interest: InterestSchema


class UserInterestSchema(BaseModel):
    id: int
    user_id: int
    sub_interest_id: SubInterestSchema
    

    class Config:
        orm_mode = True

