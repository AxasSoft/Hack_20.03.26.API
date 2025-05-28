from app.models import ExcursionBooking
from app.schemas.excursion_booking import GettingExcursionBooking
from app.schemas.excursion_member import GettingExcursionMember
from app.utils.datetime import to_unix_timestamp
from app.models import ExcursionMember, ExcursionImage
from sqlalchemy.orm import Session


def get_excursion_booking(excursion_booking: ExcursionBooking) -> GettingExcursionBooking:
    print("     *****     ", excursion_booking.excursion.category_id)
    return GettingExcursionBooking(
        id=excursion_booking.id,
        excursion_group_id=excursion_booking.group_id,
        user_id=excursion_booking.user_id,
        started=to_unix_timestamp(excursion_booking.excursion_group.started),
        ended=to_unix_timestamp(excursion_booking.excursion_group.ended),
        created=to_unix_timestamp(excursion_booking.created),
        updated_at=to_unix_timestamp(excursion_booking.updated_at),
        status=excursion_booking.status,
        comment=excursion_booking.comment,
        excursion_id=excursion_booking.excursion_id,
        excursion_category_id=excursion_booking.excursion.category_id,
        excursion_name=excursion_booking.excursion.name,
        members=[
            GettingExcursionMember(
                full_name=member.full_name,
                is_adult=member.is_adult,
                phone=member.phone
            )
            for member in excursion_booking.members
        ],
        excursion_images = [
            image.image
            for image in excursion_booking.excursion.images
        ],
    )