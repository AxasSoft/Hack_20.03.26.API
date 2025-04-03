from typing import Optional

from pydantic import BaseModel, Field

from .id_model import IdModel


class CreatingPage(BaseModel):
    tech_name: str = Field(..., title='техническое название')
    title: Optional[str] = Field(None, title='Заголовок')
    body: Optional[str] = Field(None, title='Текст')


class UpdatingPage(BaseModel):
    tech_name: Optional[str] = Field(None, title='техническое название')
    title: Optional[str] = Field(None, title='Заголовок')
    body: Optional[str] = Field(None, title='Текст')


class GettingPage(CreatingPage,IdModel):
    pass
