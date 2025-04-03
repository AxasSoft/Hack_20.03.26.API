from app.getters import get_user_short_info, get_event_category
from app.getters.interest_user import get_interest_user
from app.models import Event, EventMember, User, EventFeedback, EventPeriod
from app.schemas import GettingEvent, GettingEventMember, GettingImage, GettingPeriod
from app.utils.datetime import to_unix_timestamp
from hashlib import md5
from typing import Optional, List
from sqlalchemy.orm import Session
import datetime
from app.utils.datetime import to_unix_timestamp



def get_hash(nums: List[int]) -> str:
    return md5(':'.join(map(str, nums)).encode('utf-8')).hexdigest()



def get_event_member(event_member: EventMember) -> GettingEventMember:
    result = GettingEventMember(
        id=event_member.id,
        user=get_user_short_info(event_member.user),
        status=event_member.status,
    )
    if result.status is not None:
        result.status = result.status.value    
    return result

def get_event_period(event_period: EventPeriod) -> GettingPeriod:
    return GettingPeriod(
        started=to_unix_timestamp(event_period.started),
        ended=to_unix_timestamp(event_period.ended)
    )

def get_event(db: Session, event, current_user: Optional[User]) -> GettingEvent:

    if  isinstance(event, Event):
        period_data = None
    else:
        event, *period_data = event
        if period_data[0] is None:
            period_data = None

    if current_user is None:
        is_rated = None
        is_member = None
    else:
        is_rated = (db.query(EventFeedback)
                    .filter(EventFeedback.event_id == event.id, EventFeedback.user_id == current_user.id)
                    .first() is not None
                    )
        is_member = (
            db.query(EventMember)
            .filter(EventMember.event_id == event.id, EventMember.user_id == current_user.id)
            .first() is not None
        )

    if period_data is None:
        hid = get_hash([event.id])
        periods = [(event.started, event.ended)]
        for period in event.event_periods:
            periods.append((period.started, period.ended))

        active_period = None
        now_flag = False

        now = datetime.datetime.utcnow()

        for period in periods:
            if now_flag:
                active_period = period
                break
            if (period[0] is None or period[0] <= now) and (period[1] is None or period[1] >= now):
                now_flag = True
                break
        if active_period is None:
            if periods[0][0] > now:
                active_period = periods[0]
            else:
                active_period = periods[-1]

    else:
        hid = get_hash([event.id, period_data[0]])
        active_period = period_data[-2:]



    result = GettingEvent(
        hid=hid,
        id=event.id,
        created=to_unix_timestamp(event.created),
        name=event.name,
        description=event.description,
        # type_=event.type_,
        started=to_unix_timestamp(event.started),
        # period=event.period,
        ended=to_unix_timestamp(event.ended),
        is_private=event.is_private,
        place=event.place,
        lat=event.lat,
        lon=event.lon,
        # price=event.price,
        # start_link=event.start_link,
        # report_link=event.report_link,
        user=get_user_short_info(event.user),
        images=[
            GettingImage(
                id=image.id,
                link=image.image
            )
            for image in event.images
        ],
        members=[
            get_event_member(event_member=member)
            for member in event.event_members
        ],
        max_event_members=event.max_event_members,
        is_open=event.is_open != False,
        is_draft=event.is_draft != False,
        price=event.price,
        pay_link=event.pay_link,
        is_periodic=event.is_periodic,
        interests=[
            get_interest_user(item.interest) for item in sorted(event.event_interests, key=lambda x: x.id)
        ],
        periods=[
            get_event_period(period)
            for period
            in sorted(event.event_periods, key=lambda x: x.id)
        ],
        rating=event.rating,
        is_rated=is_rated,
        is_member=is_member,
        active_period=GettingPeriod(
            started=to_unix_timestamp(active_period[0]),
            ended=to_unix_timestamp(active_period[1]),
        ),
        membership_allowed=event.max_event_members is None or len(event.event_members) < event.max_event_members,
        age=event.age,
        category=get_event_category(event.category) if event.category else None,
        link=event.link,
        status=event.status,
        moderation_comment=event.moderation_comment
    )

    if result.status is not None:
        result.status = result.status.value
    return result