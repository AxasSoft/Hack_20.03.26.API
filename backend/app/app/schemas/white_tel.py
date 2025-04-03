import enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from .category import GettingCategory
from .id_model import IdModel


class BaseWhiteTel(BaseModel):
    tel: str
    name: Optional[str]
    comment: Optional[str]


class CreatingWhiteTel(BaseWhiteTel, BaseModel):
    pass


class UpdatingWhiteTel(BaseWhiteTel, BaseModel):
    tel: Optional[str]


class GettingWhiteTel(IdModel, BaseWhiteTel, BaseModel):
    pass