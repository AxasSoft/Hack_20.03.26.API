from typing import Optional, List

from pydantic import BaseModel, Field

from . import GettingUserShortInfo
from .id_model import IdModel


class CreatingEventFeedback(BaseModel):
    rate: Optional[int]
    text: Optional[str]


class UpdatingEventFeedback(BaseModel):
    rate: Optional[int]
    text: Optional[str]
    answer_text: Optional[str]


class GettingEventFeedback(IdModel, BaseModel):
    created: int
    user: GettingUserShortInfo
    rate: Optional[int]
    text: Optional[str]
    answer_text: Optional[str]
