from app.models import ExcursionCategory
from app.schemas.excursion_category import GettingExcursionCategory
from app.schemas.image import GettingImage
from sqlalchemy import inspect


def get_excursion_category(excursion_category: ExcursionCategory) -> GettingExcursionCategory:
    data = {c.key: getattr(excursion_category, c.key) for c in inspect(excursion_category).mapper.column_attrs}
    if excursion_category.background_image:
        first_image = excursion_category.background_image[0]
        background_image = first_image.image
    else:
        background_image = None
    result = GettingExcursionCategory(
        **data,
        background_image=background_image
    )
    return result