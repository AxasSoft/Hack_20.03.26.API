from app.getters import get_user_short_info, get_excursion_category
from app.getters.interest_user import get_interest_user
from app.getters.excursion_review import get_excursion_review
from app.models import Excursion, User, ExcursionReview
from app.schemas import GettingExcursion, GettingImage, GettingExcursionReview, GettingCPExcursion
from app.utils.datetime import to_unix_timestamp
from hashlib import md5
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import datetime
from app.utils.datetime import to_unix_timestamp



def get_hash(nums: List[int]) -> str:
    return md5(':'.join(map(str, nums)).encode('utf-8')).hexdigest()



# def get_excursion_member(excursion_member: ExcursionMember) -> GettingExcursionMember:
#     result = GettingExcursionMember(
#         id=excursion_member.id,
#         user=get_user_short_info(excursion_member.user),
#         status=excursion_member.status,
#     )
#     if result.status is not None:
#         result.status = result.status.value
#     return result
#
# def get_excursion_period(excursion_period: ExcursionPeriod) -> GettingPeriod:
#     return GettingPeriod(
#         started=to_unix_timestamp(excursion_period.started),
#         ended=to_unix_timestamp(excursion_period.ended)
#     )

def get_excursion(db: Session, excursion: Excursion) -> GettingExcursion:
    data = {c.key: getattr(excursion, c.key) for c in inspect(excursion).mapper.column_attrs}
    reviews = db.query(ExcursionReview).filter(ExcursionReview.excursion_id == excursion.id).order_by(ExcursionReview.created.desc()).limit(5).all()
    result = GettingExcursion(
        **data,
        category = get_excursion_category(db=db, excursion_category=excursion.category),
        images = [
            image.image
            for image in excursion.images
        ],
        reviews = [get_excursion_review(review) for review in reviews]
    )
    return result


def get_cp_excursion(db: Session, excursion: Excursion) -> GettingCPExcursion:
    data = {c.key: getattr(excursion, c.key) for c in inspect(excursion).mapper.column_attrs}
    reviews = db.query(ExcursionReview).filter(ExcursionReview.excursion_id == excursion.id).order_by(ExcursionReview.created.desc()).limit(5).all()
    result = GettingCPExcursion(
        **data,
        category = get_excursion_category(db=db, excursion_category=excursion.category),
        images = [
            GettingImage(
                id = image.id,
                link = image.image,
            )
            for image in excursion.images
        ],
        reviews = [get_excursion_review(review) for review in reviews]
    )
    return result