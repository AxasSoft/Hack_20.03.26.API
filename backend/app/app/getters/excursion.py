from app.getters import get_user_short_info, get_excursion_category
from app.getters.interest_user import get_interest_user
from app.models import Excursion, User, ExcursionReview
from app.schemas import GettingExcursion, GettingImage, GettingShortExcursionReview
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
    reviews = db.query(ExcursionReview).order_by(ExcursionReview.created.desc()).limit(5).all()



    result = GettingExcursion(
        **data,
        category = get_excursion_category(excursion.category),
        images = [
            GettingImage(
                id=image.id,
                link=image.image
            )
            for image in excursion.images
        ],
        rewiews = [GettingShortExcursionReview(
            id=review.id,
            visit_date=review.visit_date,
            description=review.description,
            rating=review.rating
        )
            for review in reviews

        ]
    )
    return result