from app.models.white_tel import WhiteTel
from app.schemas.white_tel import GettingWhiteTel


def get_white_tel(db_obj: WhiteTel) -> GettingWhiteTel:
    return GettingWhiteTel(
        id=db_obj.id,
        tel=db_obj.tel,
        name=db_obj.name,
        comment=db_obj.comment
    )