from typing import Optional, Union, Dict, Any, Type, List
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import text, alias, func, or_, and_, desc, not_, asc
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce
from fastapi import UploadFile, HTTPException
from app.enums.mod_status import ModStatus
from app.crud.base import CRUDBase
from app.exceptions import UnprocessableEntity
from app.enums.mod_status import ModStatus
from app.getters import get_interest_user
from app.models import User, EventMember, AcceptingStatus, EventImage, EventPeriod, EventInterest, Subscription, Interest, UserInterest, EventCategory
from app.models.event import Event
from app.schemas.event import CreatingEvent, UpdatingEvent, ModerationBody, GettingEventStats
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp
from app.enums.mod_status import ModStatus
from app.models.push_notification import PushNotification
from ..notification.notificator import Notificator


class CRUDEvent(CRUDBase[Event, CreatingEvent, UpdatingEvent]):

    def __init__(self, model: Type[Event]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def get_image_by_id(self, db: Session, id: Any):
        return db.query(EventImage).filter(EventImage.id == id).first()

    def add_image(self, db: Session, *, event: Event, image: UploadFile, num: Optional[int] = None) -> Optional[EventImage]:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'event/images/' + uuid.uuid4().hex + os.path.splitext(image.filename)[1]

        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=image.file,
            ContentType=image.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        image = EventImage()
        image.event = event
        image.image = new_url
        image.num = num
        db.add(image)

        db.commit()
        db.refresh(event)

        return image

    def delete_image(self, db: Session, *, image: EventImage) -> None:
        event = image.event
        event.updated = dt.datetime.utcnow()
        db.add(event)
        db.delete(image)
        db.commit()

    def search(
            self,
            db: Session,
            name: Optional[str] = None,
            started_from: Optional[int]= None,
            started_to: Optional[int]= None,
            ended_from: Optional[int]= None,
            ended_to: Optional[int]= None,
            price_from: Optional[int]= None,
            price_to: Optional[int]= None,
            place: Optional[str]= None,
            current_lon: Optional[float]= None,
            current_lat: Optional[float]= None,
            current_user: Optional[User] = None,
            distance: Optional[int]= None,
            page:Optional[int]= None,
            for_su: bool = False,
            is_private: Optional[bool] = None,
            user_id: Optional[int] = None,
            creator_id: Optional[int] = None,
            is_open: Optional[bool] = None,
            is_periodic: Optional[bool] = None,
            interests: Optional[List[int]] = None,
            reversed_order: Optional[bool] = False,
            collapse: Optional[bool] = True,
            statuses: Optional[List[ModStatus]] = None,
    ):
        
        if collapse is None:
            collapse = True
        if collapse:
            query = db.query(self.model).join(EventPeriod,isouter=True)
            if started_from is not None:
                query = query.filter(
                    self.model.started != None,
                    or_(
                        EventPeriod.id == None,
                        EventPeriod.started != None
                    ),
                    or_(
                        self.model.started >= from_unix_timestamp(started_from),
                        EventPeriod.started >= from_unix_timestamp(started_from)
                    )
                )

            if started_to is not None:
                query = query.filter(
                    or_(
                        self.model.started == None,
                        self.model.started <= from_unix_timestamp(started_to),
                        and_(
                            EventPeriod.id != None,
                            EventPeriod.started <= from_unix_timestamp(started_to)
                        )
                    )
                )

            if ended_from is not None:
                query = query.filter(
                    or_(
                        self.model.ended == None,
                        self.model.ended >= from_unix_timestamp(ended_from),
                        and_(
                            EventPeriod.id != None,
                            EventPeriod.ended >= from_unix_timestamp(ended_from)
                        )
                    )
                )

            if ended_to is not None:
                query = query.filter(
                    or_(
                        self.model.ended == None,
                        self.model.ended <= from_unix_timestamp(ended_to),
                        and_(
                            EventPeriod.id != None,
                            EventPeriod.ended <= from_unix_timestamp(ended_to)
                        )
                    )
                )
        else:
            active_period = alias(EventPeriod)
            period = alias(EventPeriod)
            query = (
                db.query(self.model, active_period)
                    .join(active_period, active_period.c.event_id == self.model.id, isouter=True)
                    .join(period, period.c.event_id == self.model.id, isouter=True)
            )
            if started_from is not None:
                query = query.filter(
                    self.model.started != None,
                    or_(
                        period.c.id == None,
                        period.c.started != None
                    ),
                    or_(
                        self.model.started >= from_unix_timestamp(started_from),
                        period.c.started >= from_unix_timestamp(started_from)
                    ),
                    or_(
                        active_period.c.id == None,
                        active_period.c.started >= from_unix_timestamp(started_from)
                    )
                )

            if started_to is not None:
                query = query.filter(
                    or_(
                        self.model.started == None,
                        self.model.started <= from_unix_timestamp(started_to),
                        and_(
                            period.c.id != None,
                            period.c.started <= from_unix_timestamp(started_to)
                        )
                    ),
                    or_(
                        active_period.c.id == None,
                        active_period.c.started == None,
                        active_period.c.started <= from_unix_timestamp(started_to)
                    )
                )

            if ended_from is not None:
                query = query.filter(
                    or_(
                        self.model.ended == None,
                        self.model.ended >= from_unix_timestamp(ended_from),
                        and_(
                            period.c.id != None,
                            period.c.ended >= from_unix_timestamp(ended_from)
                        )
                    ),
                    or_(
                        active_period.c.id == None,
                        active_period.c.ended == None,
                        active_period.c.ended >= from_unix_timestamp(ended_from)
                    )
                )

            if ended_to is not None:
                query = query.filter(
                    or_(
                        self.model.ended == None,
                        self.model.ended <= from_unix_timestamp(ended_to),
                        and_(
                            period.c.id != None,
                            period.c.ended <= from_unix_timestamp(ended_to)
                        )
                    ),
                    or_(
                        active_period.c.id == None,
                        active_period.c.ended == None,
                        active_period.c.ended <= from_unix_timestamp(ended_to)
                    )
                )

        if user_id is not None:
            query = query.filter(EventMember.user_id == user_id)
        
        if creator_id is not None:
            query = query.filter(Event.user_id == creator_id)

        if is_private is not None:
            query = query.filter(Event.is_private == is_private)

        if not for_su and current_user is not None and user_id is None:

            query = query.join(EventMember, isouter=True).filter(
                or_(
                    Event.is_private == False,
                    and_(
                        Event.is_private == True,
                        or_(
                            EventMember.user_id == current_user.id,
                            Event.user_id == current_user.id,
                        )
                    )
                )
            )

        if name is not None:
            query = query.filter(self.model.name.ilike(f'@{name}%'))
            
        if price_from is not None:
            query = query.filter(coalesce(self.model.price,0) >= price_from)

        if price_to is not None:
            query = query.filter(coalesce(self.model.price,0) <= price_to)

        if is_open is not None:
            query = query.filter(self.model.is_open == is_open)

        if interests is not None:
            query = query.join(EventInterest, isouter=True).filter(EventInterest.interest_id.in_(interests))

        if started_from is not None:
            query = query.filter(self.model.started >= from_unix_timestamp(started_from))

        if started_to is not None:
            query = query.filter(self.model.started <= from_unix_timestamp(started_to))

        if ended_from is not None:
            query = query.filter(self.model.ended >= from_unix_timestamp(ended_from))

        if ended_to is not None:
            query = query.filter(self.model.ended <= from_unix_timestamp(ended_to))

        if place is not None:
            query = query.filter(self.model.place.ilike(f'%{place}%'))
        
        # if (current_user is None or creator_id is None or current_user.id != creator_id) and not for_su:
        #     query = query.filter(not_(Event.is_draft))
        if is_periodic is not None:
            query = query.filter(Event.is_periodic == is_periodic)

        if statuses is not None and len(statuses) > 0:
            query = query.filter(self.model.status.in_(statuses))

        if all(x is not None for x in (current_lon, current_lat, distance,)):

            sq = db.query(
                self.model.id.label('event_id'),
                func.st_distancespheroid(
                    text('''ST_SetSRID(ST_MakePoint(event.lat, event.lon), 4326)'''),
                    text('''ST_SetSRID(ST_MakePoint(:current_lat, :current_lon), 4326)''').bindparams(
                        current_lat=current_lat,
                        current_lon=current_lon
                    ),
                ).label('d')
            ).subquery()

            # query = query.join(sq, sq.c.event_id == self.model.id,isouter=True).filter(sq.c.d < distance).order_by(sq.c.d)
            query = query.join(sq, sq.c.event_id == self.model.id,isouter=True).filter(sq.c.d < distance)
            if reversed_order:
                query = query.order_by(desc(sq.c.d), desc(self.model.started))
            else:
                query = query.order_by(sq.c.d, self.model.started)
        else:
            if reversed_order:
                query = query.order_by(desc(self.model.started))
            else:
                query = query.order_by(self.model.started)

        query = query.distinct()

        return pagination.get_page(query,page)


    def create_for_user(self, db: Session, *, obj_in: CreatingEvent, user: User, notificator) -> Event:
        db_obj = self.model()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if 'started' in update_data:
            update_data['started'] = from_unix_timestamp(update_data['started'])
        if 'ended' in update_data:
            update_data['ended'] = from_unix_timestamp(update_data['ended'])
        if 'is_open' in update_data:
            update_data['is_open'] = update_data['is_open'] != False
        if update_data['age'] is None:
            update_data['age'] = 0
        if 'category_id' in update_data and update_data['category_id'] is not None:
            query_event = db.query(EventCategory).filter(EventCategory.id == update_data['category_id']).first()
            if query_event is None:
                raise HTTPException(
                status_code=404, detail="Категория не найдена"
                )
        if 'members' in update_data:
            member_ids = update_data.pop('members')
        else:
            member_ids = []
        update_data['is_draft'] = bool(update_data.get('is_draft'))

        for field in dir(db_obj):
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db_obj.user = user

        db.add(db_obj)

        user.rating += 1
        db.add(user)

        members_max_count = db_obj.max_event_members
        if 'max_event_members' in update_data:
            members_max_count = update_data['max_event_members']

        if members_max_count is not None and len(member_ids) > members_max_count:
            raise UnprocessableEntity('Слишком много участников')

        for member_id in member_ids:
            event_member = EventMember()
            event_member.event = db_obj
            event_member.user_id = member_id
            db.add(event_member)

        db.commit()
        db.refresh(db_obj)

        if 'interests' in update_data:
            for interest_id in update_data['interests']:
                event_interest = EventInterest()
                event_interest.event = db_obj
                event_interest.interest_id = interest_id
                db.add(event_interest)
        if update_data.get('periods') is not None:
            for period in update_data['periods']:
                event_period = EventPeriod(
                    started=from_unix_timestamp(period.get('started')),
                    ended=from_unix_timestamp(period.get('ended')),
                    event=db_obj
                )
                db.add(event_period)

        db.commit()
        interests = update_data.get('interests', [])
        interested_users = (db.query(User).
            join(
                Subscription,
                and_(Subscription.subject_id == User.id, Subscription.object_id == user.id),
                isouter=True
            )
        )
        if len(interests) > 0:
            interested_users = interested_users.join(
                UserInterest,
                and_(UserInterest.user_id == User.id, UserInterest.interest_id.in_(interests)),
            )
        if len(interests) == 0:
            interested_users = interested_users.filter(User.id != None)
        elif len(interests) == 1:
            interested_users = interested_users.filter(
                or_(UserInterest.interest_id == interests[0], User.id != None))
        else:
            interested_users = interested_users.filter(
                or_(UserInterest.interest_id.in_(interests), User.id != None)
            )

        users = interested_users.all()

        #   УЫЕДОМЛЕНИЯ
        
        if len(users) > 0 and not db_obj.is_draft:

            link = 'krasnodar://event/?id=' + str(db_obj.id)
            db_push = PushNotification()
            db_push.title = 'Вам может быть интересно'
            if user.first_name is not None and user.last_name is not None:
                user_name = f'{user.first_name} {user.last_name}'
            elif user.first_name is not None:
                user_name = user.first_name
            elif user.last_name is not None:
                user_name = user.last_name
            else:
                user_name = f'#{user.id}'
            db_push.body = (f'Новое мероприятие "{db_obj.name}" от пользователя {user_name}.'
                            f' Вам может быть интересно')
            db_push.link = link
            db.add(db_push)
            db.commit()

            notificator.notify_many(
                db, recipients=users, text=db_push.body, title=db_push.title, icon=None, link=db_push.link
            )

        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Event,
        obj_in: Union[UpdatingEvent, Dict[str, Any]]
    ) -> Event:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if 'started' in update_data:
            update_data['started'] = from_unix_timestamp(update_data['started'])
        if 'ended' in update_data:
            update_data['ended'] = from_unix_timestamp(update_data['ended'])
        if 'is_open' in update_data:
            update_data['is_open'] = update_data['is_open'] != False
        if 'is_periodic' in update_data:
            update_data['is_periodic'] = bool(update_data['is_periodic'])
        for field in dir(db_obj):
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)


        if 'members' in update_data:

            member_ids = update_data.pop('members')
            member_statuses = {

            }

            members_max_count = db_obj.max_event_members
            if 'max_event_members' in update_data:
                members_max_count = update_data['max_event_members']

            if members_max_count is not None and len(member_ids) > members_max_count:
                raise UnprocessableEntity('Слишком много участников')

            for em in db.query(EventMember).filter(EventMember.event_id == db_obj.id).all():
                member_statuses[em.user_id] = em.status
                db.delete(em)

            for member_id in member_ids:
                user = db.query(User).filter(User.id == member_id)
                if user is None:
                    raise UnprocessableEntity(f'Добавленного пользователя не сушествует {member_id}')
                event_member = EventMember()
                event_member.event = db_obj
                event_member.user_id = member_id
                event_member.status = member_statuses.get(member_id, AcceptingStatus.wait)
                db.add(event_member)


        if 'interests' in update_data:

            db.query(EventInterest).filter(EventInterest.event_id == db_obj.id).delete()

            for interest_id in update_data['interests']:
                event_interest = EventInterest()
                event_interest.event = db_obj
                event_interest.interest_id = interest_id
                db.add(event_interest)
        db.commit()

        if 'periods' in update_data:
            db.query(EventPeriod).filter(EventPeriod.event_id == db_obj.id).delete()
            for period in update_data['periods']:
                event_period = EventPeriod(
                    started=from_unix_timestamp(period.get('started')),
                    ended=from_unix_timestamp(period.get('ended')),
                    event=db_obj
                )
                db.add(event_period)


        db.commit()
        db.refresh(db_obj)
        return db_obj


    def edit_member_status(self, db: Session, *, event_member: EventMember, new_status: AcceptingStatus) -> EventMember:
        event_member.status = new_status
        db.add(event_member)
        db.commit()
        db.refresh(event_member)
        return event_member


    def member_exist(self, db: Session, user_id: int, event_id: int) -> bool:
        return db.query(EventMember).filter(EventMember.user_id == user_id, EventMember.event_id == event_id).first() is not None

    def add_member(self, db: Session, user_id: int, event_id: int, status: AcceptingStatus) -> EventMember:

        event = db.query(Event).filter(Event.id == event_id).first()

        if event.max_event_members is not None and len(event.event_members) >= event.max_event_members:
            raise UnprocessableEntity('Слишком много участников')


        event_member = EventMember()
        event_member.event_id = event_id
        event_member.user_id = user_id
        event_member.status = status
        db.add(event_member)
        db.commit()
        db.refresh(event_member)
        return event_member


    def delete_member(self, db: Session, *, event_member: EventMember) -> None:
        db.delete(event_member)
        db.commit()


    def get_member(self, db: Session, event_member_id: int) -> Optional[EventMember]:
        return db.query(EventMember).filter(EventMember.id == event_member_id).first()
    
    
    def get_event_stat(self, db: Session):
        events_count = db.query(Event).count()
        members_count = db.query(EventMember).filter(EventMember.status == AcceptingStatus.accepted).count()

        count_subquery = (
            db.query(
                EventInterest.interest_id.label('interest_id'),
                func.count(EventInterest.interest_id).label('interest_count')
            )
            .join(Event, Event.id == EventInterest.event_id, isouter=False)
            .group_by(EventInterest.interest_id)
            .subquery()
        )

        top_interest = (
            db.query(EventInterest)
            .join(count_subquery, EventInterest.interest_id == count_subquery.c.interest_id)

            .order_by(count_subquery.c.interest_count.desc())
            .first()
        )
        return GettingEventStats(
            events_count=events_count,
            members_count=members_count,
            top_interest=get_interest_user(top_interest.interest) if top_interest else None
        )
   
    
    def get_members_count(self, db: Session):
        query = (db.query(Interest.name, func.count(EventMember.user_id).label("user_count"))
            .select_from(EventMember)
            .outerjoin(EventInterest, EventMember.event_id == EventInterest.event_id)
            .join(Interest, EventInterest.interest_id == Interest.id, isouter=True)
        ).group_by(Interest.name)
        res = query.all()
        return res
    

    def moderate(self, db: Session, *, event: Event, moderation_body: ModerationBody):
        event.status = moderation_body.status
        event.moderation_comment = moderation_body.comment
        db.add(event)
        db.commit()
        return event

event = CRUDEvent(Event)