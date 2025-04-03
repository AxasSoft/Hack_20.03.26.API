from typing import Optional

from pydantic import BaseModel

from . import GettingUser
from .id_model import IdModel


class InfoBase(BaseModel):
    title: Optional[str]
    body: Optional[str]
    category: Optional[int]
    important: Optional[bool]
    is_hidden: Optional[bool]
    source: Optional[str]


class GettingInfo(InfoBase, IdModel):
    created: int
    image: Optional[str]
    user: Optional[GettingUser]



class CreatingInfo(InfoBase):
    pass


class UpdatingInfo(InfoBase):
    pass
