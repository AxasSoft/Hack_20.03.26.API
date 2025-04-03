import enum
from typing import Optional, List

from app.schemas import GettingUserShortInfo
from pydantic import BaseModel, EmailStr, Field

from .id_model import IdModel


class BaseComment(BaseModel):
    text: str = Field(..., title='Текст коментария')


class CreatingComment(BaseComment):
    pass


class UpdatingComment(BaseComment):
    pass


class GettingComment(BaseComment,IdModel):
    created: int = Field(..., title="Дата создания")
    user: GettingUserShortInfo = Field(title="Автор коментария")
