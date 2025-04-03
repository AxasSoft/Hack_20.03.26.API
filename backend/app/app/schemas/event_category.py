from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel


class CreatingEventCategory(BaseModel):
    name: str


class UpdatingEventCategory(BaseModel):
    name: Optional[str]


class GettingEventCategory(IdModel, BaseModel):
    name: str