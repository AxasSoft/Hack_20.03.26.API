from typing import TypeVar, Generic, Optional, Any, List

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


class IdModel(BaseModel):
    id: int = Field(..., ge=0)