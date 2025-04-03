import enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from .category import GettingCategory
from .id_model import IdModel


class BaseBlackTel(BaseModel):
    tel: str
    name: Optional[str]
    comment: Optional[str]


class CreatingBlackTel(BaseBlackTel, BaseModel):
    pass


class UpdatingBlackTel(BaseBlackTel, BaseModel):
    tel: Optional[str]


class GettingBlackTel(IdModel, BaseBlackTel, BaseModel):
    pass