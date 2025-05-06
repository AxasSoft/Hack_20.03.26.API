from app.models import Transfer
from app.schemas import GettingTransfer
from app.utils.datetime import to_unix_timestamp
from app.getters import get_user_short_info


def get_transfer(transfer: Transfer) -> GettingTransfer:
    return GettingTransfer(
        id=transfer.id,
        created=to_unix_timestamp(transfer.created),
        type=transfer.type,
        passengers_quantity=transfer.passengers_quantity,
        child_seat=transfer.child_seat,
        animal=transfer.animal,
        ski_supplies=transfer.ski_supplies,
        comment=transfer.comment,
        user_id = transfer.user_id,
        first_name = transfer.user.first_name,
        patronymic = transfer.user.patronymic,
        last_name = transfer.user.last_name,
        tel = transfer.user.tel
    )