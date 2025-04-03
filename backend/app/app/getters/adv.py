from app.getters.adv_slide import get_adv_slide
from app.models import AdvSlide
from app.models.adv import Adv
from app.schemas.adv import GettingAdv
from app.utils.datetime import to_unix_timestamp


def get_adv(adv: Adv) -> GettingAdv:
    return GettingAdv(
        id=adv.id,
        created=to_unix_timestamp(adv.created),
        name=adv.name,
        cover=adv.cover,
        link=adv.link,
        button_name=adv.button_name,
        slides=[
            get_adv_slide(slide) for slide in adv.slides
        ]
    )
