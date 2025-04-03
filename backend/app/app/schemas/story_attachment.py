import enum
from typing import Optional

from pydantic import BaseModel, Field

from .id_model import IdModel


class GettingStoryAttachment(IdModel, BaseModel):
    main_link: str
    cover_link: Optional[str]
    is_image: bool
    created: int
