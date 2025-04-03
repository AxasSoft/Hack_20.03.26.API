from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel


class CreatingBook(BaseModel):
    name: str


class UpdatingBook(BaseModel):
    name: Optional[str]


class GettingBook(IdModel, BaseModel):
    name: str