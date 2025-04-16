from typing import Optional

from pydantic import BaseModel

from .image import GettingImage
from .id_model import IdModel


class CreatingExcursionCategory(BaseModel):
    name: str
    description: Optional[str] = None


class UpdatingExcursionCategory(CreatingExcursionCategory):
    name: Optional[str]


class GettingExcursionCategory(IdModel, CreatingExcursionCategory):
    background_image: Optional[str] = None

