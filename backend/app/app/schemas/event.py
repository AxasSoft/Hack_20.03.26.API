from typing import Optional, List

from pydantic import BaseModel, Field

from . import GettingUserShortInfo, GettingEventCategory
from .interest_user import GettingInterestUser
from .id_model import IdModel
from .image import GettingImage
from ..enums.mod_status import ModStatus
from ..models.event_member import AcceptingStatus


class CreatingPeriod(BaseModel):
    started: Optional[int]
    ended: Optional[int]


class CreatingEvent(BaseModel):
    name: Optional[str]
    description: Optional[str]
    # type_: str
    started: int
    ended: Optional[int]
    periods: Optional[List[CreatingPeriod]]
    is_private: Optional[bool]
    # price: int = Field(0)
    # start_link: Optional[str]
    # report_link: Optional[str]
    place: Optional[str]
    lat: float
    lon: float
    members: Optional[List[int]] = None
    max_event_members: Optional[int]
    is_open: Optional[bool]
    is_draft: Optional[bool]
    price: Optional[int]
    pay_link: Optional[str]
    is_periodic: Optional[bool]
    interests: Optional[List[int]]
    periods: Optional[List[CreatingPeriod]]
    category_id: Optional[int] = None
    age: Optional[int] = None
    link: Optional[str]


class UpdatingEvent(BaseModel):
    name: Optional[str]
    description: Optional[str]
    # type_: str
    started: Optional[int]
    ended: Optional[int]
    # period: Optional[str]
    is_private: Optional[bool]
    # price: int = Field(0)
    # start_link: Optional[str]
    # report_link: Optional[str]
    place: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    age: Optional[int]
    members: Optional[List[int]]
    max_event_members: Optional[int]
    is_open: Optional[bool]
    is_draft: Optional[bool]
    price: Optional[int]
    pay_link: Optional[str]
    is_periodic: Optional[bool]
    interests: Optional[List[int]]
    periods: Optional[List[CreatingPeriod]]
    category_id: Optional[int]
    link: Optional[str]


class GettingEventMember(IdModel, BaseModel):
    user: GettingUserShortInfo
    status: AcceptingStatus

class GettingPeriod(BaseModel):
    started: Optional[int]
    ended: Optional[int]

class GettingEvent(IdModel, BaseModel):
    hid: str
    created: int
    name: Optional[str]
    description: Optional[str]
    # type_: str
    started: int
    ended: Optional[int]
    period: Optional[str]
    is_private: Optional[bool]
    # price: int = Field(0)
    # start_link: Optional[str]
    # report_link: Optional[str]
    place: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    age: Optional[int]
    user: GettingUserShortInfo
    members: List[GettingEventMember]
    images: List[GettingImage]
    max_event_members: Optional[int]
    is_open: bool
    is_draft: bool
    price: Optional[int]
    pay_link: Optional[str]
    is_periodic: bool
    category: Optional[GettingEventCategory] = None
    interests: Optional[List[GettingInterestUser]]
    link: Optional[str]
    rating: Optional[float]
    is_rated: Optional[bool]
    is_member: Optional[bool]
    status: ModStatus
    moderation_comment: Optional[str]
    membership_allowed: bool
    user: GettingUserShortInfo
    



class StatusBody(BaseModel):
    status: AcceptingStatus


class CreatingEventMember(BaseModel):
    user_id: int
    status: AcceptingStatus


class ModerationBody(BaseModel):
    status: ModStatus
    comment: Optional[str]


class GettingEventStats(BaseModel):
    events_count: int
    members_count: int
    top_interest: Optional[GettingInterestUser]


class GettingEventsStatsWithMembers(BaseModel):
    type_event: Optional[str]
    count_members: Optional[int]