import datetime
from typing import Any, Dict, Optional, Union, Type, List, Tuple

from sqlalchemy import or_, not_, and_, desc
from paginate_sqlalchemy import SqlalchemyOrmPage
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from user_agents import parse

from app.crud.base import CRUDBase
from app.crud.crud_story_attachment import story_attachment as attachment_crud
from app.models import Hug, Device, FirebaseToken, FavoriteStory, Subscription
from app.models.story import Story
from app.models.user import User
from app.schemas.response import Paginator
from app.schemas.story import CreatingStory, UpdatingStory
from app.utils import pagination
from ..models import Hashtag, StoryHashtag, StoryAttachment, View, StoryHiding, UserBlock


class CRUDStory(CRUDBase[Story, CreatingStory, UpdatingStory]):

    def __init__(self, model: Type[Story]):
        super().__init__(model=model)

    def _handle_device(
            self,
            db: Session,
            owner: User,
            host: Optional[str] = None,
            x_real_ip: Optional[str] = None,
            accept_language: Optional[str] = None,
            user_agent: Optional[str] = None,
            x_firebase_token: Optional[str] = None
    ):
        device = db.query(Device).filter(
            Device.user == owner,
            Device.ip_address == host,
            Device.x_real_ip == x_real_ip,
            Device.accept_language == accept_language,
            Device.user_agent == user_agent
        ).order_by(desc(Device.created)).first()

        detected_os = None

        if user_agent is not None:
            ua_string = str(user_agent)
            ua_object = parse(ua_string)

            detected_os = ua_object.os.family
            if detected_os is None or detected_os.lower() == 'other':
                if 'okhttp' in user_agent.lower():
                    detected_os = 'Android'
                elif 'cfnetwork' in user_agent.lower():
                    detected_os = 'iOS'
                else:
                    detected_os = None

        if device is None:
            device = Device()
            device.user = owner
            device.ip_address = host
            device.x_real_ip = x_real_ip
            device.accept_language = accept_language
            device.user_agent = user_agent
            device.detected_os = detected_os
        db.add(device)

        if x_firebase_token is not None:
            firebase_token = FirebaseToken()
            firebase_token.device = device
            firebase_token.value = x_firebase_token
            db.add(firebase_token)

        db.commit()

    def create_story_by_user(self, db, *, user: User, obj_in: CreatingStory, is_short_story: bool = False):
        db_obj = Story()
        db_obj.user = user
        db_obj.text = obj_in.text
        db_obj.is_private = obj_in.is_private if obj_in.is_private is not None else None
        db_obj.is_short_story = is_short_story
        db.add(db_obj)

        user.rating += 1
        db.add(user)

        attachments = []

        if obj_in.gallery is not None:
            not_found = []
            forbidden = []
            rebinding = []
            for index, attachment_id in enumerate(obj_in.gallery):
                attachment = attachment_crud.get_by_id(db,id=attachment_id)
                if attachment is None:
                    not_found.append(index)
                    continue
                if attachment.story is not None:
                    rebinding.append(index)
                    continue
                attachments.append(attachment)
            if len(not_found) > 0:
                return None, -2, not_found
            if len(forbidden) > 0:
                return None, -3, forbidden
            if len(rebinding) > 0:
                return None, -4, rebinding

        if obj_in.video is not None:
            attachment = attachment_crud.get_by_id(db,id=obj_in.video)
            if attachment is None:
                return None, -5, None
            if attachment.user != user:
                return None, -6, None
            if attachment.story is not None:
                return None, -7, None
            attachments.append(attachment)

        for attachment in attachments:
            attachment.story = db_obj
            db.add(attachment)

        for hashtag_text in obj_in.hashtags:
            hashtag = db.query(Hashtag).filter(Hashtag.text == hashtag_text).first()
            if hashtag is None:
                hashtag = Hashtag()
                hashtag.text = hashtag_text
                db.add(hashtag)
            story_hashtag = StoryHashtag()
            story_hashtag.story = db_obj
            story_hashtag.hashtag = hashtag
            db.add(story_hashtag)

        db.commit()
        db.refresh(db_obj)

        return db_obj, 0, None


    def update(
        self,
        db: Session,
        *,
        db_obj: Story,
        obj_in:  Union[UpdatingStory, Dict[str, Any]]
    ):
        new_attachments = []
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if 'text' in update_data:
            db_obj.text = obj_in.text
        if 'is_private' in update_data:
            db_obj.is_private = obj_in.is_private if obj_in.is_private is not None else None
        db.add(db_obj)
        if 'gallery' in update_data:
            new_ids_in_gallery = update_data['gallery'] or []
            old_objs_in_gallery = db_obj.attachments.filter(StoryAttachment.is_image).all()
            old_ids_in_gallery = [item.id for item in old_objs_in_gallery]

            for_removing = []
            not_found = []
            forbidden = []
            rebinding = []

            for index, id_ in enumerate(old_ids_in_gallery):
                if id_ not in new_ids_in_gallery:
                    old_attachment = old_objs_in_gallery[index]
                    for_removing.append(old_attachment)
            for index, id_ in enumerate(new_ids_in_gallery):
                if id_ not in old_ids_in_gallery:
                    new_attachment = attachment_crud.get_by_id(db,id=id_)
                    if new_attachment is None:
                        not_found.append(index)
                    if new_attachment.story is not None:
                        rebinding.append(index)
                    new_attachment.story = db_obj
                    db.add(new_attachment)

            if len(not_found) > 0:
                return None, -2, not_found
            if len(forbidden) > 0:
                return None, -3, forbidden
            if len(rebinding) > 0:
                return None, -4, rebinding

            for attachment in for_removing:
                db.delete(attachment)

        if 'video' in update_data:
            old_video = db_obj.attachments.filter(not_(StoryAttachment.is_image)).first()
            new_video_id = update_data['video']
            if old_video is not None and old_video.id != update_data['video']:
                old_video.story = None
            if new_video_id is not None:
                new_video = attachment_crud.get_by_id(db,id=new_video_id)
                if new_video is None:
                    return None, -5, None
                if new_video.user != db_obj.user:
                    return None, -6, None
                if new_video.story is not None:
                    return None, -7, None
                new_attachments.append(new_video)

        if 'hashtags' in update_data:
            old_hashtags = {
                hashtag_text: id_
                for hashtag_text, id_
                in db.query(Hashtag.text, StoryHashtag).join(StoryHashtag).filter(StoryHashtag.story == db_obj)
            }
            new_hashtags = update_data['hashtags']

            for hashtag_text, story_hashtag in old_hashtags.items():
                if hashtag_text not in new_hashtags:
                    db.delete(story_hashtag)
            for hashtag_text in new_hashtags:
                if hashtag_text not in old_hashtags:
                    hashtag = db.query(Hashtag).filter(Hashtag.text == hashtag_text).first()
                    if hashtag is None:
                        hashtag = Hashtag()
                        hashtag.text = hashtag_text
                        db.add(hashtag)
                    story_hashtag = StoryHashtag()
                    story_hashtag.story = db_obj
                    story_hashtag.hashtag = hashtag
                    db.add(story_hashtag)

        db.commit()
        db.refresh(db_obj)
        return db_obj, 0, None

    def get_stories_by_user(
        self,
        db: Session,
        *,
        user: User,
        current_user: Optional[User] = None,
        page: Optional[int] = None,
        is_hugged: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        is_short_story: bool = False
    ) -> Tuple[List[Story], Paginator]:
        now = datetime.datetime.utcnow()
        query = db.query(Story).filter(Story.user == user).order_by(desc(Story.created))

        if is_short_story:
            query = query.filter(
                Story.is_short_story == True,
                Story.created >= now - datetime.timedelta(hours=24)
            )
        else:
            query = query.filter(Story.is_short_story == False)

        if current_user is not None:
            query = (
                query
                    .join(
                        StoryHiding,
                        and_(StoryHiding.story_id == Story.id, StoryHiding.user_id == current_user.id),
                        isouter=True
                    )
                    .join(
                        UserBlock,
                        or_(
                            and_(UserBlock.object_id == current_user.id, UserBlock.subject_id == Story.user_id),
                            and_(UserBlock.subject_id == current_user.id, UserBlock.object_id == Story.user_id)
                        ),
                        isouter=True
                    )
                    .filter(StoryHiding.id == None, UserBlock.id == None)
            )

        if current_user is not None and is_hugged is not None:
            query = query.join(Hug, and_(Hug.story_id == Story.id, Hug.user_id == current_user.id),isouter=True)
            if is_hugged:
                query = query.filter(Hug.id != None)
            else:
                query = query.filter(Hug.id == None)


        if current_user is not None and is_favorite is not None:
            query = query.join(FavoriteStory, and_(FavoriteStory.story_id == Story.id, FavoriteStory.user_id == current_user.id),isouter=True)
            if is_favorite:
                query = query.filter(FavoriteStory.id != None)
            else:
                query = query.filter(FavoriteStory.id == None)

        return pagination.get_page(query, page)


    def get_stories_from_subscriptions(
            self,
            db,
            *,
            search: Optional[str] = None,
            hashtag: Optional[Hashtag] = None,
            is_hugged: Optional[bool] = None,
            is_favorite: Optional[bool] = None,
            page: Optional[int] = None,
            is_short_story: bool = False,
            current_user: User = None,
            host: Optional[str] = None,
            x_real_ip: Optional[str] = None,
            accept_language: Optional[str] = None,
            user_agent: Optional[str] = None,
            x_firebase_token: Optional[str] = None,
    ) -> Tuple[List[Story], Paginator]:

        query = db.query(Story)
        now = datetime.datetime.utcnow()

        if search is not None:
            query = query\
                .join(StoryHashtag, isouter=True)\
                .join(Hashtag, isouter=True)\
                .filter(
                    or_(
                        Hashtag.text.ilike(f'%{search}%'),
                        Story.text.ilike(f'%{search}%')
                    )
                )

        following_user_ids = [
            row[0]
            for row
            in db.query(Subscription.object_id).filter(Subscription.subject_id == current_user.id).all()
        ]

        query = query.filter(Story.user_id.in_(following_user_ids))

        if is_short_story:
            query = query.filter(
                Story.is_short_story == True,
                Story.created >= now - datetime.timedelta(hours=24)
            )
        else:
            query = query.filter(Story.is_short_story == False)

        if hashtag is not None:
            query = query.join(StoryHashtag).filter(StoryHashtag.hashtag == hashtag)

        if current_user is not None and is_hugged is not None:
            query = query.join(Hug, and_(Hug.story_id == Story.id, Hug.user_id == current_user.id), isouter=True)
            if is_hugged:
                query = query.filter(Hug.id != None)
            else:
                query = query.filter(Hug.id == None)

        if current_user is not None and is_favorite is not None:
            query = query.join(FavoriteStory, and_(FavoriteStory.story_id == Story.id, FavoriteStory.user_id == current_user.id),isouter=True)
            if is_favorite:
                query = query.filter(FavoriteStory.id != None)
            else:
                query = query.filter(FavoriteStory.id == None)

        if current_user is not None:
            self._handle_device(
                db=db,
                owner=current_user,
                host=host,
                x_real_ip=x_real_ip,
                accept_language=accept_language,
                user_agent=user_agent,
                x_firebase_token=x_firebase_token
            )
            query = (
                query
                    .join(
                        StoryHiding,
                        and_(StoryHiding.story_id == Story.id, StoryHiding.user_id == current_user.id),
                        isouter=True
                    )
                    .join(
                        UserBlock,
                        or_(
                            and_(UserBlock.object_id == current_user.id, UserBlock.subject_id == Story.user_id),
                            and_(UserBlock.subject_id == current_user.id, UserBlock.object_id == Story.user_id)
                        ),
                        isouter=True
                    )
                    .filter(StoryHiding.id == None, UserBlock.id == None)
            )

        # query = query.filter(
        #     now - Story.created <= datetime.timedelta(days=90),
        # )

        query = query.order_by(desc(Story.created)).distinct()


        return pagination.get_page(query, page)

    def mark_story_as_viewed(
            self,
            db,
            *,
            story: Story,
            user: User
    ):
        view = db.query(View).filter(View.story == story, View.user == user).first()
        if view is None:
            view = View()
            view.user = user
            view.story = story
            db.add(view)
            db.commit()

    def hug_story(
            self,
              db,
              *,
              story: Story,
              user: User,
              hugs: bool
    ):
        hug = db.query(Hug).filter(Hug.story == story, Hug.user == user).first()
        owner_story = story.user
        
        if hug is None and hugs:
            hug = Hug()
            hug.story = story
            hug.user = user
            db.add(hug)
            if user.id != owner_story.id:
                owner_story = story.user
                owner_story.rating += 1
            db.commit()
            
        if hug is not None and not hugs:
            owner_story = story.user
            if owner_story.rating != 0:
                if user.id != owner_story.id:
                    owner_story.rating -= 1
            db.delete(hug)
            db.commit()
        
            
    def favorite_story(
                self,
                db,
                *,
                story: Story,
                user: User,
                is_favorite: bool
    ):
        fav = db.query(FavoriteStory).filter(FavoriteStory.story == story, FavoriteStory.user == user).first()
        if fav is None and is_favorite:
            fav = FavoriteStory()
            fav.story = story
            fav.user = user
            db.add(fav)
            db.commit()

        elif fav is not None and not is_favorite:
            db.delete(fav)
            db.commit()

    def hide_story(
            self,
            db,
            *,
            story: Story,
            user: User,
            hide: bool
    ):
        hiding = db.query(StoryHiding).filter(StoryHiding.story == story, StoryHiding.user == user).first()
        if hiding is None and hide:
            hiding = StoryHiding()
            hiding.story = story
            hiding.user = user
            db.add(hiding)
            db.commit()

        elif hiding is not None and not hide:
            db.delete(hiding)
            db.commit()

    def get_stories(
            self,
            db,
            *,
            search: Optional[str],
            hashtag: Optional[Hashtag],
            user: Optional[User],
            is_hugged: Optional[bool] = None,
            is_favorite: Optional[bool] = None,
            is_short_story: bool = False,
            page: Optional[int] = None,
            current_user: Optional[User] = None,
            host: Optional[str],
            x_real_ip: Optional[str],
            accept_language: Optional[str],
            user_agent: Optional[str],
            x_firebase_token: Optional[str]
    ) -> Tuple[List[Story], Paginator]:

        query = db.query(Story)
        now = datetime.datetime.utcnow()

        if is_short_story:
            query = query.filter(
                Story.is_short_story == True,
                Story.created >= now - datetime.timedelta(hours=24)
            )
        else:
            query = query.filter(Story.is_short_story == False)

        if search is not None:
            query = query \
                .join(StoryHashtag, isouter=True) \
                .join(Hashtag, isouter=True) \
                .filter(
                or_(
                    Hashtag.text.ilike(f'%{search}%'),
                    Story.text.ilike(f'%{search}%')
                )
            )

        if user is not None:
            query = query.filter(Story.user == user)
        if hashtag is not None:
            query = query.join(StoryHashtag).filter(StoryHashtag.hashtag == hashtag)

        if current_user is not None and is_hugged is not None:
            query = query.join(Hug, and_(Hug.story_id == Story.id, Hug.user_id == current_user.id), isouter=True)
            if is_hugged:
                query = query.filter(Hug.id != None)
            else:
                query = query.filter(Hug.id == None)

        if current_user is not None and is_favorite is not None:
            query = query.join(FavoriteStory, and_(FavoriteStory.story_id == Story.id, FavoriteStory.user_id == current_user.id),isouter=True)
            if is_favorite:
                query = query.filter(FavoriteStory.id != None)
            else:
                query = query.filter(FavoriteStory.id == None)

        if current_user is not None:
            self._handle_device(
                db=db,
                owner=current_user,
                host=host,
                x_real_ip=x_real_ip,
                accept_language=accept_language,
                user_agent=user_agent,
                x_firebase_token=x_firebase_token
            )
            query = (
                query
                .join(
                    StoryHiding,
                    and_(StoryHiding.story_id == Story.id, StoryHiding.user_id == current_user.id),
                    isouter=True
                )
                .join(
                    UserBlock,
                    or_(
                        and_(UserBlock.object_id == current_user.id, UserBlock.subject_id == Story.user_id),
                        and_(UserBlock.subject_id == current_user.id, UserBlock.object_id == Story.user_id)
                    ),
                    isouter=True
                )
                .filter(StoryHiding.id == None, UserBlock.id == None)
            )

        # query = query.filter(
        #     now - Story.created <= datetime.timedelta(days=90),
        # )
        query = query.order_by(desc(Story.created)).distinct()


        return pagination.get_page(query, page)

    def get_short_stories_from_subscriptions(
            self,
            db,
            *,
            page: Optional[int] = None,
            current_user: User = None,
            host: Optional[str] = None,
            x_real_ip: Optional[str] = None,
            accept_language: Optional[str] = None,
            user_agent: Optional[str] = None,
            x_firebase_token: Optional[str] = None,
    ):

        following_user_ids = [
            row[0]
            for row
            in db.query(Subscription.object_id).filter(Subscription.subject_id == current_user.id).all()
        ]

        user_ids_with_stories = (
            db.query(Story.user_id)
            .filter(
                Story.is_short_story == True,
                Story.created >= datetime.datetime.utcnow() - datetime.timedelta(hours=24),
                Story.user_id.in_(following_user_ids)
            )
            .group_by(Story.user_id)
            .order_by(func.max(Story.created).desc())  # Сортируем по дате последней истории
            .all()

        )
        user_ids = [user_id for (user_id,) in user_ids_with_stories]

        if not user_ids:
            return [], None

        query = db.query(Story)
        now = datetime.datetime.utcnow()
        query = query.filter(
            Story.is_short_story == True,
            Story.created >= now - datetime.timedelta(hours=24),
            Story.user_id.in_(following_user_ids)
        )
        if current_user is not None:
            self._handle_device(
                db=db,
                owner=current_user,
                host=host,
                x_real_ip=x_real_ip,
                accept_language=accept_language,
                user_agent=user_agent,
                x_firebase_token=x_firebase_token
            )
            query = (
                query
                .join(
                    StoryHiding,
                    and_(StoryHiding.story_id == Story.id, StoryHiding.user_id == current_user.id),
                    isouter=True
                )
                .join(
                    UserBlock,
                    or_(
                        and_(UserBlock.object_id == current_user.id, UserBlock.subject_id == Story.user_id),
                        and_(UserBlock.subject_id == current_user.id, UserBlock.object_id == Story.user_id)
                    ),
                    isouter=True
                )
                .filter(StoryHiding.id == None, UserBlock.id == None)
            )
        all_stories = query.order_by(Story.user_id, desc(Story.created)).all()

        stories_by_user: Dict[int, List[Story]] = {}
        for story in all_stories:
            if story.user_id not in stories_by_user:
                stories_by_user[story.user_id] = []
            stories_by_user[story.user_id].append(story)

        grouped_stories = [
            stories_by_user[user_id]
            for user_id in user_ids
            if user_id in stories_by_user
        ]

        if page is not None:
            items_per_page = 30
            total_items = len(grouped_stories)
            total_pages = (total_items + items_per_page - 1) // items_per_page  # Округление вверх

            # Проверка на выход за границы
            if page < 1 or (page > total_pages and total_pages > 0):
                return [], None

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_items = grouped_stories[start_idx:end_idx]

            paginator = Paginator(
                page=page,
                total=total_pages,
                has_prev=page > 1,
                has_next=page < total_pages
            )
            return paginated_items, paginator
        else:
            return grouped_stories, None

    def get_short_stories(
            self,
            db,
            *,
            page: Optional[int] = None,
            current_user: Optional[User] = None,
            host: Optional[str],
            x_real_ip: Optional[str],
            accept_language: Optional[str],
            user_agent: Optional[str],
            x_firebase_token: Optional[str]
    ) -> Tuple[List[Story], Paginator]:

        user_ids_with_stories = (
                                    db.query(Story.user_id)
                                    .filter(
                                        Story.is_short_story == True,
                                        Story.created >= datetime.datetime.utcnow() - datetime.timedelta(hours=24))
                                    .group_by(Story.user_id)
                                    .order_by(func.max(Story.created).desc())  # Сортируем по дате последней истории
                                    .all()

        )
        user_ids =[user_id for (user_id,) in user_ids_with_stories]

        if not user_ids:
            return [], None

        query = db.query(Story)
        now = datetime.datetime.utcnow()
        query = query.filter(
            Story.is_short_story == True,
            Story.created >= now - datetime.timedelta(hours=24)
        )
        if current_user is not None:
            self._handle_device(
                db=db,
                owner=current_user,
                host=host,
                x_real_ip=x_real_ip,
                accept_language=accept_language,
                user_agent=user_agent,
                x_firebase_token=x_firebase_token
            )
            query = (
                query
                .join(
                    StoryHiding,
                    and_(StoryHiding.story_id == Story.id, StoryHiding.user_id == current_user.id),
                    isouter=True
                )
                .join(
                    UserBlock,
                    or_(
                        and_(UserBlock.object_id == current_user.id, UserBlock.subject_id == Story.user_id),
                        and_(UserBlock.subject_id == current_user.id, UserBlock.object_id == Story.user_id)
                    ),
                    isouter=True
                )
                .filter(StoryHiding.id == None, UserBlock.id == None)
            )
        all_stories = query.order_by(Story.user_id, desc(Story.created)).all()

        stories_by_user: Dict[int, List[Story]] = {}
        for story in all_stories:
            if story.user_id not in stories_by_user:
                stories_by_user[story.user_id] = []
            stories_by_user[story.user_id].append(story)

        grouped_stories = [
            stories_by_user[user_id]
            for user_id in user_ids
            if user_id in stories_by_user
        ]

        if page is not None:
            items_per_page = 30
            total_items = len(grouped_stories)
            total_pages = (total_items + items_per_page - 1) // items_per_page  # Округление вверх

            # Проверка на выход за границы
            if page < 1 or (page > total_pages and total_pages > 0):
                return [], None

            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_items = grouped_stories[start_idx:end_idx]

            paginator = Paginator(
                page=page,
                total=total_pages,
                has_prev=page > 1,
                has_next=page < total_pages
            )
            return paginated_items, paginator
        else:
            return grouped_stories, None


story = CRUDStory(Story)