from app.models import SnowmobileBooking
from app.schemas import GettingSnowmobileBooking
from app.utils.datetime import to_unix_timestamp
from app.getters import get_user_short_info


def get_snowmobile_booking(snowmobile_booking: SnowmobileBooking) -> GettingSnowmobileBooking:
    return GettingSnowmobileBooking(
        id=snowmobile_booking.id,
        created=to_unix_timestamp(snowmobile_booking.created),
        started=to_unix_timestamp(snowmobile_booking.started),
        ended=to_unix_timestamp(snowmobile_booking.ended),
        snowmobile_quantity=snowmobile_booking.snowmobile_quantity,
        comment=snowmobile_booking.comment,
        user_id = snowmobile_booking.user_id,
        first_name = snowmobile_booking.user.first_name,
        patronymic = snowmobile_booking.user.patronymic,
        last_name = snowmobile_booking.user.last_name,
        tel = snowmobile_booking.user.tel
    )