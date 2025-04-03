from app.schemas.category import GettingCategory, GettingCategoryWithSubcategories
from app.getters.subcategory import get_subcategory
from app.models.category import Category


def get_category(db_obj: Category) -> GettingCategory:
    return GettingCategory(
        id=db_obj.id,
        name=db_obj.name
    )


def get_category_with_subcategories(db_obj: Category) -> GettingCategoryWithSubcategories:
    return GettingCategoryWithSubcategories(
        id=db_obj.id,
        name=db_obj.name,
        subcategories=[
            get_subcategory(sub)
            for sub in db_obj.subcategories
        ]
    )

