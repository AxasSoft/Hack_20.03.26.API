from typing import Optional

from pydantic import BaseModel

from .id_model import IdModel
from .image import GettingImage


class CreatingExcursionCategory(BaseModel):
    name: str
    description: Optional[str]


class UpdatingExcursionCategory(CreatingExcursionCategory):
    name: Optional[str]


class GettingExcursionCategory(IdModel):
    name: str
    description: Optional[str]
    # background_image: Optional[GettingImage]
