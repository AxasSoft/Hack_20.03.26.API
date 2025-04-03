from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel


class CreatingInterestUser(BaseModel):
    name: str


class UpdatingInterestUser(BaseModel):
    name: Optional[str]


class GettingInterestUser(IdModel):
    name: str