from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel


class CreatingMusic(BaseModel):
    name: str


class UpdatingMusic(BaseModel):
    name: Optional[str]


class GettingMusic(IdModel, BaseModel):
    name: str