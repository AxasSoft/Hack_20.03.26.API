from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel


class CreatingMovie(BaseModel):
    name: str


class UpdatingMovie(BaseModel):
    name: Optional[str]


class GettingMovie(IdModel, BaseModel):
    name: str