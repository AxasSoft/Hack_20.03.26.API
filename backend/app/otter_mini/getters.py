from datetime import datetime

from sqlalchemy import func

from app.getters import get_user
from app.models import User
from app.utils.datetime import to_unix_timestamp
from otter_mini.models import Chat, Message, MessageExtraDatum, Member
from otter_mini.models.contacting import Contacting
from otter_mini.schemas import GettingChat, GettingMember, GettingContacting, GettingMessage, GettingAttachment, \
    GettingMessageWithParent


def get_attachment(attachment):
    return GettingAttachment(
        id=attachment.id,
        created=to_unix_timestamp(attachment.created),
        link=attachment.link,
        type=attachment.type
    )


def get_message(
    message: Message,
    db,
    user
):
    if message.sender is not None and message.sender.user_id == user.id:
        is_read_by_me = True
    else:
        is_read_by_me = len([extra for extra in message.extra_data if extra.user_id == user.id and extra.read]) > 0
    is_read_by_members = len([extra for extra in message.extra_data if extra.user_id != user.id and extra.read]) > 0
    if message.is_delete:
        is_deleted = True
    else:
        is_deleted = len([extra for extra in message.extra_data if extra.user_id == user.id and extra.is_delete]) > 0
    return GettingMessage(
        id=message.id,
        created=to_unix_timestamp(message.created),
        is_event=message.is_event,
        body=message.body,
        is_read_by_me=is_read_by_me,
        is_read_by_members=is_read_by_members,
        sender=get_user(db, message.sender.user, user),
        attachments=[get_attachment(attachment) for attachment in message.attachments],
        is_deleted=is_deleted
    )


def get_message_with_parent(message, db, user):
    return GettingMessageWithParent(
        **get_message(message, db, user).dict(),
        parent=get_message(message.parent, db, user) if message.parent is not None else None
    )


def get_chat(member,db,user):
    chat: Chat = member.chat
    chat_type: str = chat.type_
    if chat_type == 'personal':
        member_count = 2
    elif chat_type.startswith('service'):
        member_count = 1
    else:
        member_count = chat.member_count

    unread_count = member.unread_count
    if chat_type != 'personal':
        second_user = None
        chat_cover = chat.chat_cover if chat.chat_cover is not None else member.chat_cover
        chat_name = chat.chat_name if chat.chat_name is not None else member.chat_name
    else:
        if chat.initiator_id == user.id:
            second_user = chat.recipient
        else:
            second_user = chat.initiator
        chat_name = member.chat_name if member.chat_name is not None else ' '.join(
            name
            for name
            in [
                second_user.last_name,
                second_user.first_name,
                second_user.patronymic,
            ]
            if name is not None
        )
        chat_cover = member.chat_cover if member.chat_cover is not None else second_user.avatar

    return GettingChat(
            id=chat.id,
            type=chat_type,
            subtype=chat.subtype,
            number=chat.number,
            name=chat_name,
            cover=chat_cover,
            member_count=member_count,
            unread_count=unread_count if unread_count > 0 else 0,
            second_user=get_user(db,second_user, user) if second_user is not None else None,
            first_message_id=member.first_message_id,
            last_message=get_message_with_parent(
                member.last_message,
                db,
                user
            ) if member.last_message is not None else None
        )

def get_chat_for_admin(chat, db, user):
    chat_type: str = chat.type_
    if chat_type == 'personal':
        member_count = 2
    elif chat_type.startswith('service'):
        member_count = 1
    else:
        member_count = chat.member_count

    tech_member = db.query(Member).filter(Member.is_tech, Member.chat_id == chat.id).first()
    if tech_member is None:
        chat_data = db.query(func.count(Message.id), func.max(Message.id), func.min(Message.id)).join(Member, Message.sender_id == Member.id, isouter=False).first()
        if chat_data is None:
            unread_count = 0
            last_message_id = None
            first_message_id = None
        else:
            unread_count = chat_data[0]
            last_message_id = chat_data[1]
            first_message_id = chat_data[2]
        if last_message_id is None:
            last_message = None
        else:
            last_message = db.query(Message).get(last_message_id)

        first_superuser = db.query(User).filter(User.is_superuser).order_by(User.id).first()
        tech_member = Member()
        tech_member.user = first_superuser
        tech_member.is_tech = True
        tech_member.chat = chat
        tech_member.unread_count = unread_count
        tech_member.last_message_id = last_message_id
        db.add(tech_member)
        db.commit()
    else:
        first_message_id = tech_member.first_message_id
        last_message = tech_member.last_message
        unread_count = tech_member.unread_count



    if chat_type != 'personal':

        chat_cover = chat.chat_cover
        chat_name = chat.chat_name
    else:
        if chat.initiator is None and chat.recipient is None:
            chat_name = None
            chat_cover = None
        elif chat.recipient is None:
            chat_name = ' '.join(
                name
                for name
                in [
                    chat.initiator.last_name,
                    chat.initiator.first_name,
                    chat.initiator.patronymic,
                ]
                if name is not None
            )
            chat_cover = chat.initiator.avatar
        elif chat.initiator is None:
            chat_name = ' '.join(
                name
                for name
                in [
                    chat.recipient.last_name,
                    chat.recipient.first_name,
                    chat.recipient.patronymic,
                ]
                if name is not None
            )
            chat_cover = chat.recipient.avatar
        else:
            chat_name = ' '.join(
                name
                for name
                in [
                    chat.initiator.last_name,
                    chat.initiator.first_name,
                    chat.initiator.patronymic,
                ]
                if name is not None
            ) + ' и ' + ' '.join(
                name
                for name
                in [
                    chat.recipient.last_name,
                    chat.recipient.first_name,
                    chat.recipient.patronymic,
                ]
                if name is not None
            )
            chat_cover = chat.initiator.avatar

    return GettingChat(
        id=chat.id,
        type=chat_type,
        subtype=chat.subtype,
        number=chat.number,
        name=chat_name,
        cover=chat_cover,
        member_count=member_count,
        unread_count=unread_count,
        second_user=None,
        first_message_id=first_message_id,
        last_message=get_message_with_parent(
            last_message,
            db,
            user
        ) if last_message is not None else None
    )

def get_member(member, db, user):
    return GettingMember(
        id=member.id,
        created=to_unix_timestamp(member.created),
        user=get_user(db,member.user,user)
    )

def get_contacting(contacting: Contacting, db, user):
    return GettingContacting(
        id=contacting.id,
        created=to_unix_timestamp(contacting.created),
        body=contacting.body,
        back_contacts=contacting.back_contacts,
        processed=to_unix_timestamp(contacting.processed),
        user=get_user(db,contacting.user,user) if user is not None and contacting.user is not None else None
    )