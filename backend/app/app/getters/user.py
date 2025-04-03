from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.getters.category import get_category
from app.getters.timestamp import to_timestamp
from app.models import UserBlock
from app.models import device, Story, Hug, User, PushNotification
from app.schemas.user import (
    GettingUser,
    GettingUserShortInfo,
    GettingUserWithAdminInfo,
    GettingUserShortAdminInfo,
    AdminInfo,
    Device, GettingPushNotification
)
from app.utils.datetime import humanize_last_visited, to_unix_timestamp


def get_user(db: Session, db_obj, db_user: Optional[User]) -> GettingUser:

    """
    Получить данные пользователя в формате схемы личного профиля
    """


    result = GettingUser(
        id=db_obj.id,
        email=db_obj.email if db_obj.email is not None else db_obj.shadow_email,
        tel=db_obj.tel if db_obj.tel is not None else db_obj.shadow_tel,
        is_active=db_obj.is_active,
        is_superuser=db_obj.is_superuser,
        first_name=db_obj.first_name,
        patronymic=db_obj.patronymic,
        last_name=db_obj.last_name,
        birthtime=to_timestamp(db_obj.birthtime),
        avatar=db_obj.avatar,
        gender=db_obj.gender,
        location=db_obj.location,
        rating=db_obj.rating or 0,
        count_feedback_order=db_obj.count_feedback_order or 0,
        created_orders_count=db_obj.created_orders_count or 0,
        completed_orders_count=db_obj.completed_orders_count or 0,
        my_offers_count=db_obj.my_offers_count or 0,
        stories_count=db_obj.stories.count(),
        hugs_count=db.query(Hug).join(Story).filter(Story.user == db_obj).count(),
        last_visited=to_timestamp(db_obj.last_visited),
        last_visited_human=humanize_last_visited(db_obj.last_visited),
        is_online=db_obj.last_visited is not None and datetime.utcnow() - db_obj.last_visited < timedelta(minutes=5),
        i_block=(db.query(UserBlock).filter(UserBlock.subject==db_user,UserBlock.object_==db_obj).first() is not None) if (db_user is not None) else False,
        block_me=(db.query(UserBlock).filter(UserBlock.subject==db_obj,UserBlock.object_==db_user).first() is not None) if (db_user is not None) else False,
        category_id=db_obj.category_id,
        category=get_category(db_obj.category) if db_obj.category is not None else None,
        is_servicer=db_obj.is_servicer or False,
        tg=db_obj.tg,
        in_blacklist=db_obj.in_blacklist,
        in_whitelist=db_obj.in_whitelist,
        in_subscriptions=len([sub for sub in db_obj.object_subscriptions if sub.subject == db_user]) > 0,
        is_business=db_obj.is_business,
        show_tel=db_obj.show_tel if db_obj.show_tel is not None else True,
        region=db_obj.region,
        site=db_obj.site,
        experience=db_obj.experience,
        company_info=db_obj.company_info,
        lat=db_obj.lat,
        lon=db_obj.lon,
        country=db_obj.country,
        status=db_obj.status,
        subscriptions_count=db_obj.subscriptions_count,
        subscribers_count=db_obj.subscribers_count,
        profile_cover=db_obj.profile_cover,
        is_dating_profile=db_obj.is_dating_profile or False,
        # dating_profile_id=db_obj.dating_profile_id,
        is_editor=db_obj.is_editor,
        is_support=db_obj.is_support,
    )
    if result.gender is not None:
        result.gender = result.gender.value
    return result


def get_user_short_info(db_obj) -> GettingUserShortInfo:

    result = GettingUserShortInfo(
        id=db_obj.id,
        email=db_obj.email if db_obj.email is not None else db_obj.shadow_email,
        tel=db_obj.tel if db_obj.tel is not None else db_obj.shadow_tel,
        is_active=db_obj.is_active,
        is_superuser=db_obj.is_superuser,
        first_name=db_obj.first_name,
        patronymic=db_obj.patronymic,
        last_name=db_obj.last_name,
        birthtime=to_timestamp(db_obj.birthtime),
        avatar=db_obj.avatar,
        gender=db_obj.gender,  # .value if db_obj.gender is not None else None,
        location=db_obj.location,
        rating=db_obj.rating,
        last_visited=to_timestamp(db_obj.last_visited),
        last_visited_human=humanize_last_visited(db_obj.last_visited),
        is_online=db_obj.last_visited is not None and datetime.utcnow() - db_obj.last_visited < timedelta(minutes=5),
        category_id=db_obj.category_id,
        category=get_category(db_obj.category) if db_obj.category is not None else None,
        is_servicer=db_obj.is_servicer or False,
        tg=db_obj.tg,
        in_blacklist=db_obj.in_blacklist,
        in_whitelist=db_obj.in_whitelist,
        is_business=db_obj.is_business,
        show_tel=db_obj.show_tel if db_obj.show_tel is not None else True,
        region=db_obj.region,
        lat=db_obj.lat,
        lon=db_obj.lon,
        country=db_obj.country,
        status=db_obj.status,
        subscriptions_count=db_obj.subscriptions_count,
        subscribers_count=db_obj.subscribers_count,
        profile_cover=db_obj.profile_cover,
        is_dating_profile=db_obj.is_dating_profile,
        # dating_profile_id=db_obj.dating_profile_id,
        is_editor=db_obj.is_editor,
        is_support=db_obj.is_support,
    )
    if result.gender is not None:
        result.gender = result.gender.value
    return result


def get_device(db_obj):

    return Device(
        id=db_obj.id,
        accept_language=db_obj.accept_language,
        user_agent=db_obj.user_agent,
        created=int((db_obj.created if db_obj.created is not None else datetime.utcnow()).timestamp()),
        ip_address=db_obj.ip_address,
        x_real_ip=db_obj.x_real_ip,
        detected_os=db_obj.detected_os
    )


def _get_admin_info( db_obj) -> AdminInfo:
    last_device = db_obj.devices.order_by(desc(device.Device.created)).first()
    return AdminInfo(
        device=get_device(last_device) if last_device is not None else None,
        created=int((db_obj.created if db_obj.created is not None else datetime.utcnow()).timestamp()),
        deleted=int(db_obj.deleted.timestamp()) if db_obj.deleted is not None else None,
    )


def get_user_short_admin_info(db_obj) -> GettingUserShortAdminInfo:
    return GettingUserShortAdminInfo(
        **get_user_short_info(db_obj).dict(),
        **_get_admin_info(db_obj).dict()
    )


def get_user_with_admin_info(db: Session, db_obj) -> GettingUserWithAdminInfo:

    return GettingUserWithAdminInfo(
        **get_user(db, db_obj,None).dict(),
        **_get_admin_info(db_obj).dict()
    )


def get_push_notification(push_notification: PushNotification) -> GettingPushNotification:
    return GettingPushNotification(
        id=push_notification.id,
        title=push_notification.title,
        body=push_notification.body,
        created=to_unix_timestamp(push_notification.created),
        link=push_notification.link
    )