from app.models.adv_slide import AdvSlide
from app.schemas.adv_slide import GettingAdvSlide


def get_adv_slide(adv_slide: AdvSlide) -> GettingAdvSlide:
    return GettingAdvSlide(
        id=adv_slide.id,
        title=adv_slide.title,
        body=adv_slide.body,
        img=adv_slide.img
    )
