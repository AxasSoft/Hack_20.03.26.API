from app.models import ExcursionCategory
from app.schemas import GettingExcursionCategory
from app.schemas.image import GettingImage


def get_excursion_category(excursion_category: ExcursionCategory) -> GettingExcursionCategory:
    if excursion_category.background_image:
        first_image = excursion_category.background_image[0]
        background_image = GettingImage(
            id=first_image.id, link=first_image.image
        )
    else:
        background_image = None
    category_data = {
        "id": excursion_category.id,
        "name": excursion_category.name,
        "description": excursion_category.description,
        # "background_image": background_image
    }
    return GettingExcursionCategory(
        **category_data
    )