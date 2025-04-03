from typing import List

from pydantic import BaseModel, Field

from .subcategory import GettingSubcategory
from .id_model import IdModel


class CategoryBase(BaseModel):
    name: str = Field(..., title="Название темы")


class GettingCategory(CategoryBase, IdModel):
    pass


class CreatingCategory(CategoryBase):
    pass


class UpdatingCategory(CategoryBase):
    pass

class GettingCategoryWithSubcategories(GettingCategory):
    subcategories: List[GettingSubcategory]


