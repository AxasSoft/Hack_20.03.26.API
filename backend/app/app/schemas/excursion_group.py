from typing import Optional, List
from pydantic import BaseModel, Field

from .id_model import IdModel
from ..enums.group_status import GroupStatus
from .excursion_member import GettingExcursionMember


class CreatingExcursionGroup(BaseModel):
    started: int
    ended: Optional[int]


class UpdatingExcursionGroup(CreatingExcursionGroup):
    pass


class GettingExcursionGroup(IdModel, CreatingExcursionGroup):
    status: Optional[GroupStatus]
    excursion_id: int
    excursion_name: str
    max_group_size: int
    available_for_booking: int
    current_members: int
    members: List[GettingExcursionMember]

class UpdatingStatusExcursionGroup(BaseModel):
    status: Optional[GroupStatus]