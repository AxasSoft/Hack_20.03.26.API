from app.models import ExcursionCategory
from app.schemas.excursion_category import GettingExcursionCategory
from app.schemas.image import GettingImage
from app import crud
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def get_excursion_category(db: Session, excursion_category: ExcursionCategory) -> GettingExcursionCategory:
    data = {c.key: getattr(excursion_category, c.key) for c in inspect(excursion_category).mapper.column_attrs}
    print(excursion_category.background_image)
    if excursion_category.background_image:
        background_image = crud.crud_excursion_category.excursion_category.get_last_image(db=db, excursion_category=excursion_category).image
    else:
        background_image = None
    result = GettingExcursionCategory(
        **data,
        background_image=background_image
    )
    return result