from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel


class InfoBase(BaseModel):
    title: Optional[str]
    body: Optional[str]
    link: Optional[str]



class GettingServiceInfo(InfoBase, IdModel):
    created: int
    updated: int
    image: Optional[str]


class CreatingServiceInfo(InfoBase):
    slug: str


class UpdatingServiceInfo(InfoBase):
    slug: Optional[str]
