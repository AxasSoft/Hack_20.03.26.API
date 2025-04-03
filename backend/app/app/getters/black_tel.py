from app.models.black_tel import BlackTel
from app.schemas.black_tel import GettingBlackTel


def get_black_tel(db_obj: BlackTel) -> GettingBlackTel:
    return GettingBlackTel(
        id=db_obj.id,
        tel=db_obj.tel,
        name=db_obj.name,
        comment=db_obj.comment
    )