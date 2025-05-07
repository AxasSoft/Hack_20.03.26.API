from typing import List

from app.models import ExcursionGroup
from app.schemas import GettingExcursionGroup, GettingExcursionMember
from app.utils.datetime import to_unix_timestamp
from app.models import ExcursionMember
from sqlalchemy.orm import Session


def get_excursion_group(db: Session,excursion_group: ExcursionGroup) -> GettingExcursionGroup:
    def get_members(db: Session, excursion_group: ExcursionGroup) -> List[ExcursionMember]:
        query = db.query(ExcursionMember).filter(ExcursionMember.excursion_group_id == excursion_group.id)
        members = query.all()
        return members


    members_data = [] if excursion_group.current_members == 0 else get_members(db=db, excursion_group=excursion_group)
    return GettingExcursionGroup(
        id=excursion_group.id,
        started=to_unix_timestamp(excursion_group.started),
        ended=to_unix_timestamp(excursion_group.ended),
        status=excursion_group.status,
        excursion_id=excursion_group.excursion_id,
        excursion_name=excursion_group.excursion.name,
        max_group_size=excursion_group.excursion.max_group_size,
        available_for_booking=excursion_group.excursion.max_group_size - excursion_group.current_members,
        current_members=excursion_group.current_members,
        members=[
            GettingExcursionMember(
                full_name=member.full_name,
                is_adult=member.is_adult,
                phone=member.phone
            )
            for member in members_data
        ]
    )