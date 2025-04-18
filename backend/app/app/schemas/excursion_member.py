from typing import Optional

from pydantic import BaseModel



class CreatingExcursionMember(BaseModel):
    full_name: str
    is_adult: bool
    phone: Optional[int]


class UpdatingExcursionMember(CreatingExcursionMember):
    full_name: Optional[str]
    is_adult: Optional[bool]
    


class GettingExcursionMember(CreatingExcursionMember):
    pass
