from app.getters import get_user_short_info
from app.models import Offer
from app.schemas import GettingOffer
from app.utils.datetime import to_unix_timestamp


def get_offer(offer: Offer) -> GettingOffer:
    return GettingOffer(
        id=offer.id,
        created=to_unix_timestamp(offer.created),
        user=get_user_short_info(db_obj=offer.user),
        order_id=offer.order_id,
        is_winner=offer.is_winner,
        text=offer.text,
        address=offer.address,
        type=offer.type
    )
