from typing import Optional, List

from pydantic import BaseModel

from app.schemas.adv_slide import GettingAdvSlide


class BaseAdv(BaseModel):
    name: Optional[str]
    link: Optional[str]
    button_name: Optional[str]


class CreatingAdv(BaseAdv):
    pass


class UpdatingAdv(BaseAdv):
    pass


class GettingAdv(BaseAdv):
    id: int
    created: int
    cover: Optional[str]
    slides: List[GettingAdvSlide]
