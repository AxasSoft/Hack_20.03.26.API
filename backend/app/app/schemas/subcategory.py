from pydantic import BaseModel, Field

from .id_model import IdModel


class SubcategoryBase(BaseModel):
    name: str


class GettingSubcategory(SubcategoryBase, IdModel):
    pass


class CreatingSubcategory(SubcategoryBase):
    category_id: int


class UpdatingSubcategory(SubcategoryBase):
    category_id: int
