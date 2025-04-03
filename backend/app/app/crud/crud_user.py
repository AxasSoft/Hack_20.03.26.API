import csv
import datetime
import io
import logging
import os
import time
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional, Union, Type, List, Tuple

import requests
from botocore.client import BaseClient
from dateutil.relativedelta import relativedelta
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import cast, String, or_, not_, desc, select, func, and_, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from user_agents import parse

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_token, ALGORITHM
from app.crud.base import CRUDBase
from app.models.device import Device
from app.models.firebase_token import FirebaseToken
from app.models.user import User
from app.models.message import Message
from app.models.rating_weights import RatingWeights
from app.models.dating_profile_like import ProfileLike
from app.models.dating_profile_facts import ProfileFacts
from app.models.chat import Chat
from app.models.dating_profile_genre_music import ProfileGenreMusic
from app.models.dating_profile_interests import ProfileInterests
from app.models.attachment import Attachment
from app.models.deleted_message import DeletedMessage
from app.schemas.response import Paginator
from app.schemas.user import UpdatingUser, UpdatingUserByAdmin, CreatingPushNotification, \
    GettingStat, ByCategorySchema, CreatingUser, Gender
from ..exceptions import UnprocessableEntity
from ..models import UserBlock, PushNotification, WhiteTel, BlackTel, Notification, Order, Story, Info, Subscription
from ..notification.notificator import Notificator
from ..utils import pagination, security
from ..utils.datetime import from_unix_timestamp


class CRUDUser(CRUDBase[User, CreatingUser, UpdatingUser]):

    def __init__(self, model: Type[User]):
        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
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

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower()).first()

    def get_by_tel(self, db: Session, *, tel: str) -> Optional[User]:
        return db.query(User).filter(User.tel == tel).first()



    def authenticate(
            self,
            db: Session,
            *,
            email: str,
            password: str,
            host: Optional[str],
            x_real_ip: Optional[str],
            accept_language: Optional[str],
            user_agent: Optional[str],
            x_firebase_token: Optional[str]
    ) -> Optional[User]:
        user = self.get_by_email(db, email=email.lower())
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None

        self._handle_device(
            db=db,
            owner=user,
            host=host,
            x_real_ip=x_real_ip,
            accept_language=accept_language,
            user_agent=user_agent,
            x_firebase_token=x_firebase_token
        )

        return user



    def change_password(self, db: Session, *, email, new_password) -> int:
        user = self.get_by_email(db, email=email.lower())
        if not user:
            return -1

        user.hashed_password = get_password_hash(new_password)

        db.add(user)
        db.commit()
        db.refresh(user)

        return 0

    def send_change_email_link(self, db: Session, *, old_email, new_email, link_base) -> int:

        if old_email.lower() == new_email.lower():
            return 0

        current_user = self.get_by_email(db, email=old_email.lower())
        if not current_user:
            return -1

        conflicting_user = self.get_by_email(db, email=new_email.lower())
        if conflicting_user:
            return -2

        token = create_token(
            current_user.id,
            token_type="email",
            email=new_email.lower(),
            expires_delta=timedelta(hours=24)
        )

        link = link_base + token

        template_path = os.path.join(settings.EMAIL_TEMPLATES_DIR, 'change_email.html')

        if os.path.isfile(template_path) and self.email_sender is not None:
            body = self.email_sender.render_template(template_path, {'name': current_user.full_name, 'link': link})
            self.email_sender.send_one('Добро пожалоовать в Potogal', new_email.lower(), body)
        else:
            logging.error('Не удалось инициировать отправку почты')

    def change_email_by_token(self, db: Session, *, token) -> int:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[ALGORITHM]
            )
        except ExpiredSignatureError:
            return -2
        except JWTError:
            return -1

        subject = payload['sub']
        new_email = payload['email'].lower()

        user = self.get_by_id(db, id=subject)

        if not user:
            return -3
        conflicting_user = self.get_by_email(db, email=new_email.lower())
        if conflicting_user:
            return -4

        user.email = new_email.lower()

        db.add(user)
        db.commit()
        db.refresh(user)

        return 0

    def change_avatar(self, db: Session, *, user: User, new_avatar: Optional[UploadFile]) -> bool:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_avatar = user.avatar

        new_url = None

        if new_avatar is not None:

            name = 'users/avatars/' + uuid.uuid4().hex + os.path.splitext(new_avatar.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=new_avatar.file,
                ContentType=new_avatar.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False


        user.avatar = new_url
        db.add(user)
        db.commit()
        db.refresh(user)
        if old_avatar is not None and old_avatar.startswith(url_prefix):
            key = old_avatar[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def change_profile_cover(self, db: Session, *, user: User, new_profile_cover: Optional[UploadFile]) -> bool:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        old_profile_cover = user.profile_cover

        new_url = None

        if new_profile_cover is not None:

            name = 'users/profile_covers/' + uuid.uuid4().hex + os.path.splitext(new_profile_cover.filename)[1]

            new_url = url_prefix + name

            result = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=new_profile_cover.file,
                ContentType=new_profile_cover.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False

        user.profile_cover = new_url
        db.add(user)
        db.commit()
        db.refresh(user)
        logging.info(user.profile_cover)
        if old_profile_cover is not None and old_profile_cover.startswith(url_prefix):
            key = old_profile_cover[len(url_prefix):]
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
        return True

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def exists(self, db: Session, *, email: str) -> bool:
        return self.get_by_email(db, email=email.lower()) is not None

    def search_users(
            self,
            db: Session,
            *,
            search: Optional[str],
            sorting: Optional[str] = 'default',
            is_active: Optional[bool] = None,
            is_superuser: Optional[bool] = None,
            in_blacklist: Optional[bool] = None,
            in_whitelist: Optional[bool] = None,
            region: Optional[str] = None,
            location: Optional[str] = None,
            category_id: Optional[int] = None,
            rating_from: Optional[float] = None,
            rating_to: Optional[float] = None,
            page: Optional[int] = None,
            is_editor: Optional[bool] = None,
            is_support: Optional[bool] = None,
    ) -> Tuple[List[User], Optional[Paginator]]:

        users = db.query(User)

        if search is not None:
            search_query = f'%{search}%'

            users = users.filter(
                or_(
                    cast(User.id, String).ilike(search_query),
                    User.email.ilike(search_query),
                    User.tel.ilike(search_query),
                    func.concat(User.last_name, ' ', User.first_name, ' ', User.patronymic).ilike(search_query)
                ),
            )

        if is_active is not None:
            users = users.filter(User.is_active == is_active)
        if is_superuser is not None:
            users = users.filter(User.is_superuser == is_superuser)
        if in_blacklist is not None:
            users = users.filter(User.in_blacklist == in_blacklist)
        if in_whitelist is not None:
            users = users.filter(User.in_whitelist == in_whitelist)
        if region is not None:
            users = users.filter(User.region.ilike(region))
        if location is not None:
            users = users.filter(User.location.ilike(location))
        if category_id is not None:
            users = users.filter(User.category_id == category_id)
        if rating_from is not None:
            users = users.filter(User.rating >= rating_from)
        if rating_to is not None:
            users = users.filter(User.rating <= rating_to)

        
        if is_editor is not None:
            users = users.filter(or_(User.is_editor, User.is_superuser) == is_editor)
        if is_support is not None:
            users = users.filter(or_(User.is_support, User.is_superuser) == is_support)

        sortable = {
            'default': User.id,
            'id': User.id,
            'created': User.created,
            'deleted': User.deleted,
            'is_superuser': User.is_superuser,
            'is_active': User.is_active,
            'email': User.email,
            'detected_os': select(Device.detected_os).where(Device.user_id == User.id).order_by(Device.created).limit(
                1).subquery()
        }

        if sorting is None:
            users = users.order_by(sortable['default'])
        elif sorting[0] == '-':
            if sorting[1:] not in sortable:
                users = users.order_by(sortable['default'])
            else:
                users = users.order_by(desc(sortable[sorting[1:]]))
        else:
            if sorting not in sortable:
                users = users.order_by(sortable['default'])
            else:
                users = users.order_by(sortable[sorting])



        return pagination.get_page(users, page)

    def search_users_by_user(
            self,
            db: Session,
            *,
            search: Optional[str],
            region: Optional[str] = None,
            location: Optional[str] = None,
            category_id: Optional[int] = None,
            rating_from: Optional[float] = None,
            rating_to: Optional[float] = None,
            current_lon: Optional[float]= None,
            current_lat: Optional[float]= None,
            distance: Optional[int]= None,
            is_business: Optional[bool] = None,
            category_ids: Optional[List[int]] = None,
            page: Optional[int] = None
    ) -> Tuple[List[User], Optional[Paginator]]:
        users = db.query(User)

        if search is not None:
            search_query = f'%{search}%'

            users = users.filter(
                or_(
                    cast(User.id, String).ilike(search_query),
                    User.email.ilike(search_query),
                    User.tel.ilike(search_query),
                    func.concat(User.last_name, ' ', User.first_name, ' ', User.patronymic).ilike(search_query),
                    User.tel.ilike(search_query)
                ),
            )

        if region is not None:
            users = users.filter(User.region.ilike(region))
        if location is not None:
            users = users.filter(User.location.ilike(location))
        if category_id is not None:
            users = users.filter(User.category_id == category_id)
        if rating_from is not None:
            users = users.filter(User.rating >= rating_from)
        if rating_to is not None:
            users = users.filter(User.rating <= rating_to)
        if is_business is not None:
            users = users.filter(User.is_business == is_business)
        if category_ids is not None:
            users = users.filter(User.category_id.in_(category_ids))
        if all(x is not None for x in (current_lon, current_lat, distance,)):

            sq = db.query(
                self.model.id.label('user_id'),
                func.st_distancespheroid(
                    text('''ST_SetSRID(ST_MakePoint("user".lat, "user".lon), 4326)'''),
                    text('''ST_SetSRID(ST_MakePoint(:current_lat, :current_lon), 4326)''').bindparams(
                        current_lat=current_lat,
                        current_lon=current_lon
                    ),
                ).label('d')
            ).subquery()

            users = users.join(sq, sq.c.user_id == self.model.id,isouter=True).filter(sq.c.d < distance).order_by(sq.c.d)
        users = users.filter(User.is_active == True)
        users = users.order_by(User.id)
        return pagination.get_page(users, page)

    def update_user_by_admin(self, db: Session, *, user: User, new_data: UpdatingUserByAdmin):

        if isinstance(new_data, dict):
            update_data = new_data
        else:
            update_data = new_data.dict(exclude_unset=True)

        if 'birthtime' in update_data:
            update_data['birthtime'] = from_unix_timestamp(update_data['birthtime'])

        if 'email' in update_data and update_data['email'] is not None:
            if len(update_data['email']) == 0:
                update_data["email"] = None
            elif user.email != update_data["email"]:
                u = db.query(User).filter(User.email == update_data["email"]).first()
                if u is not None:
                    raise UnprocessableEntity('Пользователь с таким email уже существует')

        if 'tel' in update_data and update_data['tel'] is not None:
            if len(update_data['tel']) == 0:
                update_data["tel"] = None
            elif user.tel != update_data["tel"]:
                u = db.query(User).filter(User.tel == update_data["tel"]).first()
                if u is not None:
                    raise UnprocessableEntity('Пользователь с таким телефоном уже существует')

        if 'in_whitelist' not in update_data and \
                'tel' in update_data and \
                update_data['tel'] is not None and \
                db.query(WhiteTel).filter(WhiteTel.tel == update_data['tel']).first() is not None:

            update_data['in_whitelist'] = True

        if 'in_blacklist' not in update_data and \
                'tel' in update_data and \
                update_data['tel'] is not None and \
                db.query(BlackTel).filter(BlackTel.tel == update_data['tel']).first() is not None:

            update_data['in_blacklist'] = True


        for field in dir(user):
            if field in update_data:
                setattr(user, field, update_data[field])
        db.add(user)
        db.commit()
        db.refresh(user)

        if user.in_whitelist is not None:
            white_tel = db.query(WhiteTel).filter(WhiteTel.tel == user.tel).first()
            if user.in_whitelist and white_tel is None:
                white_tel = WhiteTel()
                white_tel.tel = user.tel
                db.add(white_tel)
                db.commit()
            if not user.in_whitelist and white_tel is not None:
                db.delete(white_tel)
                db.commit()
        if user.in_blacklist is not None:
            black_tel = db.query(BlackTel).filter(BlackTel.tel == user.tel).first()
            if user.in_blacklist and black_tel is None:
                black_tel = BlackTel()
                black_tel.tel = user.tel
                db.add(black_tel)
                db.commit()
            if not user.in_blacklist and black_tel is not None:
                db.delete(black_tel)
                db.commit()

        return user

    def delete_user(self, db: Session, *, user: User):
        # user.shadow_email = user.email
        # user.shadow_tel = user.tel
        # user.email = None
        # user.tel = None
        # user.deleted = datetime.datetime.utcnow()
        # user.is_active = False
        # db.add(user)
        # db.commit()
        for user_subscription in user.object_subscriptions:
            user_subscription.subject.subscriptions_count -= 1
            db.add(user_subscription.subject)
        for user_subscription in user.subject_subscriptions:
            user_subscription.object_.subscribers_count -= 1
            db.add(user_subscription.object_)

        for member in user.member:
            print(member.id)
            member.first_message_id = None
            member.last_message_id = None
            member.delete_before_id = None
            db.add(member)
            db.commit()
            db.query(DeletedMessage).filter(DeletedMessage.member_id == member.id).delete()

            messages = db.query(Message).filter(Message.sender_id == member.id).all()
            for message in messages:

                db.query(Attachment).filter(Attachment.message_id == message.id).delete()

                db.query(DeletedMessage).filter(DeletedMessage.message_id == message.id).delete()

            db.query(Message).filter(Message.sender_id == member.id).delete()

            db.query(Chat).filter(
                (Chat.initiator_id == member.id) | (Chat.recipient_id == member.id)
            ).delete()

            db.delete(member)

        dating = user.dating_profile
        if dating is not None:
            db.query(RatingWeights).filter(RatingWeights.profile_id == dating.id).delete()
            db.query(RatingWeights).filter(RatingWeights.user_id == dating.id).delete()
            db.query(ProfileFacts).filter(ProfileFacts.dating_profile_id == dating.id).delete()
            db.query(ProfileInterests).filter(ProfileInterests.dating_profile_id == dating.id).delete()
            db.query(ProfileGenreMusic).filter(ProfileGenreMusic.dating_profile_id == dating.id).delete()
            db.query(ProfileLike).filter(or_(ProfileLike.liker_dating_profile_id == dating.id,
                                            ProfileLike.liked_dating_profile_id == dating.id)).delete()
            db.delete(dating)

        db.delete(user)
        db.commit()

    def get_user_devices(self, db: Session, *, user: User, page: Optional[int] = None):
        return pagination.get_page(user.devices.order_by(Device.created), page)


    def block_user(self, db: Session, subject: User, object_: User, block: bool):
        user_block = db.query(UserBlock).filter(UserBlock.object_ == object_, UserBlock.subject == subject).first()
        if block and user_block is None:
            user_block = UserBlock()
            user_block.object_ = object_
            user_block.subject = subject
            db.add(user_block)
            db.commit()
        if not block and user_block is not None:
            db.delete(user_block)
            db.commit()


    def get_country_by_tel(self, tel):
        return None

        url = f"https://api3.greensms.ru/hlr/send?to={tel}&user=AllPortugal&pass=dcyhzv7P"

        payload = {}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            data = response.json()
            print(data)
            request_id = data['request_id']
            if request_id is None:
                raise ValueError()
        except:
            return None

        stop = False
        country = None
        while not stop:
            url = f"https://api3.greensms.ru/hlr/status?&user=AllPortugal&pass=dcyhzv7P&id={request_id}&to={tel}"

            payload = {}
            headers = {}

            response = requests.request("POST", url, headers=headers, data=payload)

            try:
                data = response.json()
                if data.get('status') != 'Status not ready':
                    stop = True
                else:
                    time.sleep(0.1)
                    continue
                print(data)
                country = data['cn']
                if country is None:
                    raise ValueError()
            except:
                return None

        return country


    def create_or_get_by_tel(self, db: Session, tel: str):
        model = self.model
        user = db.query(model).filter(model.tel == tel).first()
        if user is None:

            wt = db.query(WhiteTel).filter(WhiteTel.tel == tel).first()
            user = User()
            user.tel = tel
            if wt is not None:
                user.in_whitelist = True

            bt = db.query(BlackTel).filter(BlackTel.tel == tel).first()
            user = User()
            user.tel = tel
            if bt is not None:
                user.in_blacklist = True

            user.country = self.get_country_by_tel(tel)



        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def handle_device(
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

    def get_token(self, user: User):
        return security.create_access_token(subject=user.id)

    def create(self, db: Session, *, obj_in: CreatingUser) -> User:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
            self,
            db: Session,
            *,
            db_obj: User,
            obj_in: Union[UpdatingUser, UpdatingUserByAdmin, Dict[str, Any]]
    ) -> User:

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if 'birthtime' in update_data:
            update_data['birthtime'] = from_unix_timestamp(update_data['birthtime'])

        if 'email' in update_data and update_data['email'] is not None:
            if len(update_data['email']) == 0:
                update_data["email"] = None
            elif db_obj.email != update_data["email"]:
                u = db.query(User).filter(User.email == update_data["email"]).first()
                if u is not None:
                    raise UnprocessableEntity('Пользователь с таким email уже существует')
        
        if 'tel' in update_data and update_data['tel'] is not None:
            if len(update_data['tel']) == 0:
                update_data["tel"] = None
            elif db_obj.tel != update_data["tel"]:
                u = db.query(User).filter(User.tel == update_data["tel"]).first()
                if u is not None:
                    raise UnprocessableEntity('Пользователь с таким телефоном уже существует')

        if 'in_whitelist' not in update_data and \
            'tel' in update_data and \
            update_data['tel'] is not None and \
            db.query(WhiteTel).filter(WhiteTel.tel == update_data['tel']).first() is not None:

            update_data['in_whitelist'] = True

        if 'in_blacklist' not in update_data and \
                'tel' in update_data and \
                update_data['tel'] is not None and \
                db.query(BlackTel).filter(BlackTel.tel == update_data['tel']).first() is not None:

            update_data['in_blacklist'] = True


        for field in dir(db_obj):
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        if db_obj.in_whitelist is not None:
            white_tel = db.query(WhiteTel).filter(WhiteTel.tel == db_obj.tel).first()
            if db_obj.in_whitelist and white_tel is None:
                white_tel = WhiteTel()
                white_tel.tel = db_obj.tel
                db.add(white_tel)
                db.commit()
            if not db_obj.in_whitelist and white_tel is not None:
                db.delete(white_tel)
                db.commit()
        if db_obj.in_blacklist is not None:
            black_tel = db.query(BlackTel).filter(BlackTel.tel == db_obj.tel).first()
            if db_obj.in_blacklist and black_tel is None:
                black_tel = BlackTel()
                black_tel.tel = db_obj.tel
                db.add(black_tel)
                db.commit()
            if not db_obj.in_blacklist and black_tel is not None:
                db.delete(black_tel)
                db.commit()
        
        return db_obj

    def push_notify(self, db: Session, *, notificator: Notificator, push: CreatingPushNotification):
        db_push = PushNotification()
        db_push.title = push.title
        db_push.body = push.body
        db_push.link = push.link
        db.add(db_push)
        db.commit()

        users = db.query(self.model).all()

        notificator.notify_many(db, recipients=users, text=push.body, title=push.title, icon=None, link=push.link)

        return db_push

    def get_push_history(
            self,
            db: Session,
            *,
            page: Optional[int]
    ):
        query = db.query(PushNotification)
        query = query.order_by(desc(PushNotification.created))

        return pagination.get_page(query, page=page)

    def get_notifications(
            self,
            db: Session,
            *,
            user: User,
            page: Optional[int]
    ):
        query = db.query(Notification).filter(
            Notification.user == user,
            or_(
                not_(Notification.is_read),
                and_(
                    Notification.is_read,
                    datetime.datetime.utcnow() - Notification.created <= datetime.timedelta(days=7)
                )
            )
        )

        query = query.order_by(Notification.is_read, desc(Notification.created))

        return pagination.get_page(query, page=page)

    def mark_notification_as_read(self, db: Session, *, notification: Notification, is_read: bool):
        notification.is_read = is_read
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification


    def export(self, db: Session):

        writer_file =  io.StringIO()

        outcsv = csv.writer(writer_file)

        cursor = db\
            .execute(str(db.query(self.model).order_by(self.model.id).statement.compile(dialect=postgresql.dialect())))\
            .cursor

        # dump column titles (optional)
        outcsv.writerow(x[0] for x in cursor.description)
        # dump rows
        outcsv.writerows(cursor.fetchall())



        return writer_file.getvalue().encode()


    def stat(self, db: Session):
        start_month = datetime.datetime.utcnow() + relativedelta(day=1) + relativedelta(hour=0, minute=0, second=0, microsecond=0)
        end_month = start_month + relativedelta(months=1)

        return GettingStat(
            user_total_count=db.query(User).count(),
            user_current_count=db.query(User).filter(User.created >= start_month, User.created < end_month).count(),
            compatriot_current_count=db.query(User).filter(User.created >= start_month, User.created <= end_month, User.is_compatriot == True).count(),
            not_compatriot_current_count=db.query(User).filter(User.created >= start_month, User.created <= end_month, or_(User.is_compatriot == False, User.is_compatriot == None)).count(),
            compatriot_total_count=db.query(User).filter(User.is_compatriot == True).count(),
            not_compatriot_total_count=db.query(User).filter(or_(User.is_compatriot == False, User.is_compatriot == None)).count(),
            order_current_count=db.query(Order).filter(Order.created >= start_month, Order.created < end_month).count(),
            order_completed_count=db.query(Order).filter(Order.confirmed_at != None, Order.confirmed_at >= start_month, Order.confirmed_at < end_month).count(),
            order_total_count=db.query(Order).count(),
            story_current_count=db.query(Story).filter(Story.created >= start_month, Story.created < end_month).count(),
            story_total_count=db.query(Story).count(),
            current_info_by_category=[
                ByCategorySchema(
                    category_id=row[1],
                    count=row[0]
                )
                for row in db.query(func.count('*'), Info.category)
                    .filter(Info.created >= start_month, Info.created < end_month)
                    .group_by(Info.category)
            ],
            total_info_by_category=[
                ByCategorySchema(
                    category_id=row[1],
                    count=row[0]
                )
                for row in db.query(func.count('*'), Info.category)
                .group_by(Info.category)
            ],
            white_tel_count=db.query(WhiteTel).count(),
            black_tel_count=db.query(BlackTel).count(),
        )


    def subscribe(self, db: Session, *, subject: User, object_: User, new_value: bool):
        subscription = db.query(Subscription).filter(Subscription.object_ == object_, Subscription.subject == subject).first()
        if new_value and subscription is None:
            subscription = Subscription()
            subscription.subject = subject
            subscription.object_ = object_
            db.add(subscription)
            subject.subscriptions_count += 1
            db.add(subject)
            object_.subscribers_count += 1
            object_.rating += 1
            db.add(object_)
            db.commit()
            db.refresh(subscription)
            db.refresh(object_)
        if not new_value and subscription is not None:
            db.delete(subscription)
            subject.subscriptions_count -= 1
            db.add(subject)
            object_.subscribers_count -= 1
            if object_.rating != 0:
                object_.rating -= 1
            db.add(object_)
            db.commit()
            db.refresh(object_)

    def get_subscriptions(self, db: Session, *, user: User, page: Optional[int] = None,):
        query = db.query(Subscription).filter(
            and_(
                Subscription.subject_id == user.id,
                Subscription.object_.has(User.deleted.is_(None))
            )
        )
        # [s.object_ for s in user.subject_subscriptions if s.object_.deleted == None]
        return pagination.get_page(query, page)

    def get_subscribers(self, db: Session, *, user: User, page: Optional[int] = None,):
        query = db.query(Subscription).filter(
            and_(
                Subscription.object_id == user.id,
                Subscription.subject.has(User.deleted.is_(None))
            )
        )
        # return [s.subject for s in user.object_subscriptions if s.subject.deleted == None]
        return pagination.get_page(query, page)
    
    def create(self, db: Session, *, obj_in: CreatingUser) -> User:
        obj_in_data = jsonable_encoder(obj_in)
        if 'gender' in obj_in_data and obj_in_data['gender'] is not None:
            obj_in_data['gender'] = Gender(obj_in_data['gender'])
        if 'birthtime' in obj_in_data and obj_in_data['birthtime'] is not None:
            obj_in_data['birthtime'] = from_unix_timestamp(obj_in_data['birthtime'])
        obj_in_data['is_editor'] = obj_in_data.get('is_editor', False)
        obj_in_data['is_support'] = obj_in_data.get('is_support', False)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser(User)
