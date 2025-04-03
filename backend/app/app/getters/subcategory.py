from app.schemas.subcategory import GettingSubcategory
from app.models.subcategory import Subcategory



def get_subcategory(db_obj: Subcategory) -> GettingSubcategory:
    return GettingSubcategory(
        id=db_obj.id,
        name=db_obj.name
    )

