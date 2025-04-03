import os
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import UploadFile
from sqlalchemy import not_, or_, func, update, and_, alias, text, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from app.exceptions import UnprocessableEntity
from app.models import User, Notification
from app.utils.datetime import from_unix_timestamp
from app.utils.pagination import get_page
from otter_mini.getters import get_chat, get_member, get_attachment, get_message, get_message_with_parent, \
    get_chat_for_admin
from otter_mini.models import Member, Chat, Message, Attachment, MessageExtraDatum
from otter_mini.models.contacting import Contacting
from otter_mini.schemas import CreatingServiceChat, CreatingContacting, CreatingGroupChat, CreatingMessageWithParent, \
    MessagesBody


class CrudChat:

    def get_contacting(self, db, contacting_id):
        return db.query(Contacting).filter(Contacting.id == contacting_id).first()

    def get_contactings(self, db: Session, user_id: Optional[int], is_processed: Optional[bool], page: Optional[int]):
        query = db.query(Contacting)

        if is_processed is not None:
            query = query.filter((Contacting.processed != None) == is_processed)

        if user_id is not None:
            query = query.filter(Contacting.user_id == user_id)

        query = query.order_by((Contacting.processed != None), Contacting.created.desc())

        data, paginator = get_page(query=query, page=page)
        return data, paginator

    def create_contacting(self, db: Session, data: CreatingContacting):
        contacting = Contacting()
        contacting.body = data.body
        contacting.back_contacts = data.back_contacts
        db.add(contacting)
        db.commit()
        return contacting

    def process_contacting(self, db: Session, contacting: Contacting, user: User):
        contacting.user = user
        contacting.processed = datetime.utcnow()
        db.add(contacting)
        db.commit()
        return contacting

    def get_chat_for_user(
            self,
            db: Session, user: User,
            page: Optional[int],
            types: Optional[List[str]] = None,
            subtypes: Optional[List[str]] = None
    ):
        if types is None:
            types = []
        if subtypes is None:
            subtypes = []

        if len(subtypes) > 0 and 'service' not in types:
            types.append('service')

        query = (
            db.query(Member).join(Message, Member.last_message_id == Message.id, isouter=True)
            .filter(
                Member.user_id == user.id,
                Member.ended == None,
                Member.chat_id != None,
                not_(Member.is_tech)
            )
        )

        types = {*types}
        subtypes = {*subtypes}
        if types or subtypes:
            query = query.join(
                Chat
            )
        if types:
            query = query.filter(Chat.type_.in_(types))
        if subtypes:

            if "group" in types or 'personal' in types:
                query = query.filter(or_(Chat.subtype == None, Chat.subtype.in_(subtypes)))
            else:
                query = query.filter(Chat.subtype.in_(subtypes))

        query = query.order_by(desc(coalesce(Message.created, Member.created)))

        data, paginator = get_page(query=query, page=page)
        return [get_chat(member, db, user) for member in data], paginator

    def get_unread_count(self, db: Session, user_id):
        data = db.query(func.sum(Member.unread_count)).filter(Member.user_id == user_id, Member.ended == None).first()
        if data is None:
            return 0
        return data[0]

    def get_chat_members(self, db: Session, member: Member, page: Optional[int]):
        now = datetime.utcnow()
        chat = member.chat
        user = member.user
        chat_type: str = chat.type_
        query = db.query(Member).filter(Member.chat_id == chat.id, not_(Member.is_tech))
        if chat_type == 'personal':
            query = query.filter(Member.user_id.in_([chat.initiator_id, chat.recipient_id]))
        if chat_type.startswith('service'):
            query = query.filter(Member.user_id == chat.initiator_id)
        else:
            query = db.query(Member).filter(
                or_(Member.started == None, Member.started <= now),
                or_(Member.ended == None, Member.ended >= now)
            )

        query = query.order_by(Member.created)

        data, paginator = get_page(query=query, page=page)
        return [get_member(member, db, user) for member in data], paginator

    def create_service_chat(self, db: Session, data: CreatingServiceChat, user: User):
        number = (
            db.query(
                coalesce(func.max(Chat.number), 0) + 1)
            .filter(
                Chat.type_ == 'service',
                Chat.subtype == data.subtype
            ).scalar()
        )
        chat = Chat()
        chat.type_ = 'service'
        chat.subtype = data.subtype
        chat.number = number
        chat.chat_name = "Тех. поддержка. " + data.subtype
        chat.initiator_id = user.id
        db.add(chat)

        now = datetime.utcnow()

        chat_member = Member()
        chat_member.user = user
        chat_member.chat = chat
        chat_member.started = now
        db.add(chat_member)

        first_superuser = db.query(User).filter(User.is_superuser).order_by(User.id).first()
        if first_superuser is not None:
            tech_member = Member()
            tech_member.user = first_superuser
            tech_member.chat = chat
            tech_member.is_tech = True
            db.add(tech_member)
        else:
            tech_member = None
        db.commit()
        if data.first_message is not None:
            first_message = Message()
            first_message.body = data.first_message.body
            first_message.sender = chat_member
            db.add(first_message)
            db.commit()
            chat_member.last_message = first_message
            chat_member.unread_count = 1
            db.add(chat_member)
            if tech_member is not None:
                tech_member.last_message = first_message
                tech_member.first_message_id = first_message.id
                tech_member.unread_count = 1
                db.add(tech_member)
            db.add(first_message)
        else:
            first_message = None
        db.commit()
        if first_message is not None:
            db.refresh(first_message)
            if data.first_message.attachment_ids is not None and len(data.first_message.attachment_ids) > 0:
                db.execute(
                    update(Attachment)
                    .where(
                        and_(
                            Attachment.id.in_(data.first_message.attachment_ids),
                            Attachment.message_id == None,
                            Attachment.user_id == user.id
                        ),
                    )
                    .values(message_id=first_message.id)
                )

        db.refresh(chat)
        db.refresh(chat_member)
        return get_chat(chat_member, db, user)

    def upload_attachments(self, db: Session, data: List[UploadFile], user: User, bucket_name, s3_client):

        attachments = []

        for datum in data:

            host = s3_client._endpoint.host

            url_prefix = host + '/' + bucket_name + '/'

            name = 'event/images/' + uuid.uuid4().hex + os.path.splitext(datum.filename)[1]

            new_url = url_prefix + name

            result = s3_client.put_object(
                Bucket=bucket_name,
                Key=name,
                Body=datum.file,
                ContentType=datum.content_type
            )

            if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                continue

            attachment = Attachment()
            attachment.user = user
            attachment.type = datum.content_type
            attachment.link = new_url
            db.add(attachment)
            attachments.append(attachment)

        db.commit()
        return [
            get_attachment(attachment) for attachment in attachments
        ]

    def create_group_chat(self, db: Session, data: CreatingGroupChat, user: User):

        members = {*data.user_ids, user.id}

        chat = Chat()
        chat.type_ = 'group'
        chat.chat_name = data.chat_name
        chat.initiator_id = user.id
        chat.member_count = len(members)

        current_member = None

        db.add(chat)

        now = datetime.utcnow()

        for user_id in members:

            member = Member()
            member.chat = chat
            member.user_id = user_id
            member.started = now
            db.add(member)
            if user_id == user.id:
                current_member = member

        db.commit()
        return get_chat(current_member, db, user)

    def change_cover(self, db: Session, member: Member, cover, user: User, bucket_name, s3_client):
        host = s3_client._endpoint.host

        url_prefix = host + '/' + bucket_name + '/'

        name = 'event/images/' + uuid.uuid4().hex + os.path.splitext(cover.filename)[1]

        new_url = url_prefix + name

        result = s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=cover.file,
            ContentType=cover.content_type
        )

        chat = member.chat

        if chat.type_ == 'group':
            chat.chat_cover = new_url
            db.add(chat)
        else:
            member.chat_cover = new_url
            db.add(member)

        db.commit()

        return get_chat(member, db, user)

    def change_name(self, db: Session, member: Member, name, user: User):

        chat = member.chat

        if chat.type_ == 'group':
            chat.chat_name = name
            db.add(chat)
        else:
            member.chat_name = name
            db.add(member)

        db.commit()

        return get_chat(member, db, user)

    def find_member(self, db: Session, chat_id: int, user: User):
        now = datetime.utcnow()
        return (db.query(Member)
                .filter(
            Member.chat_id == chat_id,
            Member.user_id == user.id,
            or_(Member.ended == None, Member.ended >= now)
        ).first()
                )

    def find_tech_member(self, db: Session, chat_id: int):


        tech_member = db.query(Member).filter(Member.is_tech, Member.chat_id == chat_id).first()
        if tech_member is None:
            chat_data = db.query(
                func.count(Message.id),
                func.max(Message.id),
                func.min(Message.id)
            ).join(Member, Message.sender_id == Member.id, isouter=False).first()
            if chat_data is None:
                unread_count = 0
                last_message_id = None
                first_message_id = None
            else:
                unread_count = chat_data[0]
                last_message_id = chat_data[1]
                first_message_id = chat_data[2]


            first_superuser = db.query(User).filter(User.is_superuser).order_by(User.id).first()
            tech_member = Member()
            tech_member.user = first_superuser
            tech_member.is_tech = True
            tech_member.chat = chat_id
            tech_member.unread_count = unread_count
            tech_member.last_message_id = last_message_id
            tech_member.first_message_id = first_message_id
            db.add(tech_member)
            db.commit()

        return tech_member

    def add_members(self, db: Session, member, new_ids):
        existing_ids = [
            row[0]
            for row
            in db.query(Member.user_id)
            .filter(not_(Member.is_tech), Member.chat_id == member.chat_id, Member.user_id.in_(new_ids))
            .all()
        ]
        now = datetime.utcnow()
        adding_ids = {m for m in new_ids if m not in existing_ids}
        for user_id in adding_ids:
            new_member = Member()
            new_member.chat_id = member.chat_id
            new_member.user_id = user_id
            new_member.started = now
            db.add(new_member)
        member.chat.member_count += len(adding_ids)
        db.add(member.chat)
        db.commit()

    def remove_members(self, db: Session, member, old_ids):
        existing_ids = [
            row[0]
            for row
            in db.query(Member.id)
            .filter(
                not_(Member.is_tech),
                Member.chat_id == member.chat_id,
                Member.user_id.in_(old_ids)
            ).distinct()
            .all()
        ]

        if len(existing_ids) > 0:
            for member in db.query(Member).filter(Member.id.in_(existing_ids)):
                member.ended = datetime.utcnow()
                member.first_message_id = None
                member.last_message_id = None
                member.unread_count = 0
                db.add(member)

            if member.chat.type_ == 'group':
                member.chat.member_count -= len(existing_ids)
            db.add(member.chat)
            db.commit()

    def create_personal_chat(self, db: Session, current_user: User, second_user: User):
        initiator_alias = alias(User)
        recipient_alias = alias(User)
        chat = (
            db.query(Chat)
            .join(initiator_alias, Chat.initiator_id == initiator_alias.c.id, isouter=False)
            .join(recipient_alias, Chat.recipient_id == recipient_alias.c.id, isouter=False)
            .filter(
                Chat.type_ == 'personal',
                or_(
                    and_(
                        initiator_alias.c.id == current_user.id,
                        recipient_alias.c.id == second_user.id
                    ),
                    and_(
                        Chat.initiator_id == second_user.id,
                        Chat.recipient_id == current_user.id
                    ),
                ),

            )
            .first()
        )
        # if chat is not None:
        #     second_member = db.query(Member).filter(
        #         Member.chat_id == chat.id,
        #         Member.user_id == second_user.id
        #     ).first()
        #     # if second_member is not None:
        #     #     if second_member.ended is not None and second_member.ended < datetime.utcnow():
        #     #         raise UnprocessableEntity(message='Собеседник завершил чат')
        if chat is None:
            chat = Chat()
            chat.initiator_id = current_user.id
            chat.recipient_id = second_user.id
            chat.type_ = 'personal'
            chat.member_count = 2
            chat.chat_name = ' '.join(
                name
                for name
                in [
                    second_user.last_name,
                    second_user.first_name,
                    second_user.patronymic,
                ]
                if name is not None
            )
            chat.chat_cover = second_user.avatar
            db.add(chat)
            db.commit()
            for user in (current_user, second_user):
                member = Member()
                member.chat_id = chat.id
                member.user_id = user.id
                member.started = datetime.utcnow()
                db.add(member)
            db.commit()
        current_member = db.query(Member).filter(
            Member.chat_id == chat.id,
            Member.user_id == current_user.id
        ).first()
        if current_member is not None and current_member.ended is not None:
            current_member.started = datetime.utcnow()
            current_member.ended = None
            db.add(current_member)
        second_member = db.query(Member).filter(
            Member.chat_id == chat.id,
            Member.user_id == second_user.id
        ).first()
        if second_member is not None and second_member.ended is not None:
            second_member.started = datetime.utcnow()
            second_member.ended = None
            db.add(second_member)
        db.commit()

        return get_chat(current_member, db, current_user)

    def get_messages(
            self,
            db: Session,
            member: Member,
            start_id: Optional[int] = None,
            limit: int = 30,
            mode: Optional[str] = None,
            sorting: Optional[str] = None,
            with_equals: Optional[bool] = None,
            timestamp: Optional[int] = None,
    ):
        if with_equals is None:
            with_equals = True
        if mode is None:
            mode = 'before'
        if limit is None:
            limit = 30
        user = member.user
        started = member.started if member.started is not None else member.created
        ended = member.ended

        query = (
            db.query(Message)
            .join(
                MessageExtraDatum,
                and_(MessageExtraDatum.message_id == Message.id, MessageExtraDatum.user_id == user.id),
                isouter=True
            ).join(Member, Message.sender_id == Member.id, isouter=True).filter(
                Member.chat_id == member.chat_id,
                or_(MessageExtraDatum.id == None, not_(MessageExtraDatum.is_delete)),
                not_(Message.is_delete)
            )
        )
        if started is not None:
            query = query.filter(Message.created >= started)
        if ended is not None:
            query = query.filter(Message.created <= ended)
        if start_id is not None and mode == 'after':
            if with_equals:
                query = query.filter(Message.id >= start_id)
            else:
                query = query.filter(Message.id > start_id)
            query = query.order_by(Message.id)
        if start_id is not None and mode == 'before':
            if with_equals:
                query = query.filter(Message.id <= start_id)
            else:
                query = query.filter(Message.id < start_id)
            query = query.order_by(desc(Message.id))
        if timestamp is not None and mode == 'after':
            if with_equals:
                query = query.filter(Message.created >= from_unix_timestamp(timestamp))
            else:
                query = query.filter(Message.created > from_unix_timestamp(timestamp))
            query = query.order_by(Message.id)
        if timestamp is not None and mode == 'before':
            if with_equals:
                query = query.filter(Message.created <= from_unix_timestamp(timestamp))
            else:
                query = query.filter(Message.created < from_unix_timestamp(timestamp))
            query = query.order_by(desc(Message.id))

        if limit is not None:
            query = query.limit(limit)

        messages = query.all()

        messages = sorted(messages, key=lambda message: message.created, reverse=sorting != 'old')
        return [get_message_with_parent(message, db, user) for message in messages]

    def send_message(self, db: Session, member: Member, data: CreatingMessageWithParent, user: Optional[User] = None):
        now = datetime.utcnow()
        message = Message()
        message.sender_id = member.id
        message.parent_id = data.parent_id
        message.user_id = user.id if user is not None else member.user_id
        message.body = data.body
        db.add(message)
        db.commit()
        db.refresh(message)
        if data.attachment_ids is not None and len(data.attachment_ids) > 0:
            for attachment_id in data.attachment_ids:

                attachment = db.query(Attachment).get(attachment_id)
                if attachment is None:
                    continue
                attachment.message_id = message.id
                db.add(attachment)
            db.commit()
        user_ids = []
        for chat_member in db.query(Member).filter(Member.chat_id == member.chat_id):
            if chat_member.first_message_id == None:
                chat_member.first_message_id = message.id
            chat_member.last_message_id = message.id
            if chat_member.user_id != member.user_id:
                chat_member.unread_count += 1
            db.add(chat_member)
            if chat_member.user_id not in user_ids:
                user_ids.append(chat_member.user_id)
        db.commit()
        for user_id in user_ids:
            extra = MessageExtraDatum()
            extra.message_id = message.id
            extra.user_id = user_id
            extra.read = datetime.utcnow() if user_id == member.user_id else None
            db.add(extra)
        db.commit()
        db.refresh(message)
        print("message attachments", message.attachments)
        return get_message_with_parent(message, db, member.user)

    def read_messages(self, db: Session, member: Member, data: MessagesBody):

        extra_map = {
            message.id: (message, extra)
            for message, extra in
            (
                db.query(Message, MessageExtraDatum)
                .join(
                    MessageExtraDatum,
                    and_(
                        MessageExtraDatum.message_id == Message.id,
                        MessageExtraDatum.user_id == member.user_id
                    ),
                    isouter=True
                )
                .filter(
                    not_(Message.is_delete),
                    or_(MessageExtraDatum.id == None, not_(MessageExtraDatum.is_delete)),
                    Message.id.in_(data.messages)
                )
            )
        }

        need_update = False
        for message, extra in extra_map.values():

            if extra is not None and extra.read is not None:
                continue
            if message.sender_id == member.id:
                continue

            if extra is None:
                extra = MessageExtraDatum()
                extra.message_id = message.id
                extra.user_id = member.user_id
            extra.read = datetime.utcnow()
            db.add(extra)
            need_update = True
        db.commit()
        if need_update:
            first_message_id = (
                db.query(Message.id)
                .join(
                    MessageExtraDatum,
                    and_(
                        Message.id == MessageExtraDatum.message_id,
                        MessageExtraDatum.user_id == member.user_id
                    )
                ).filter(MessageExtraDatum != None, MessageExtraDatum.read == None)
                .first()
            )
            member.first_message_id = first_message_id[0] if first_message_id is not None else None
            db.add(member)
            db.commit()

        for notification in db.query(Notification).filter(Notification.user_id == member.user_id, Notification.link == f'portugal://chat?id={member.chat_id}'):
            notification.is_read = True
            db.add(notification)
        for member_item in member.chat.members:
            unread_count_row = (
                db.query(func.count(Message.id))
                .join(Member, Message.sender_id == Member.id)
                .join(
                    MessageExtraDatum,
                    and_(
                        MessageExtraDatum.message_id == Message.id,
                        MessageExtraDatum.user_id == member_item.user_id
                    ),
                    isouter=True
                ).filter(
                    Member.chat_id == member_item.chat_id,
                    Member.user_id != member_item.user_id,
                    or_(MessageExtraDatum.id == None, not_(MessageExtraDatum.is_delete)),
                    not_(Message.is_delete),
                    or_(MessageExtraDatum.id == None, MessageExtraDatum.read == None),
                )
            )
            print(unread_count_row.statement.compile(compile_kwargs={"literal_binds": True}))
            unread_count_row = unread_count_row.first()
            member_item.unread_count = unread_count_row[0] if unread_count_row is not None else 0
            db.add(member_item)
        db.commit()

    def delete_messages(self, db: Session, member: Member, ids: List[int], for_all: Optional[bool] = None):
        if for_all is None:
            for_all = False
        if for_all:
            members = (
                db.query(Member).filter(
                    Member.chat_id == member.chat_id,
                    or_(Member.ended == None, Member.ended <= datetime.utcnow()),
                    not_(Member.is_tech)
                ).all()
            )
            db.execute(
                update(Message)
                .where(Message.id.in_(ids))
                .values(is_delete=True)
            )
        else:
            members = (member,)
            message_map = {
                message.id: (message, extra)
                for message, extra
                in (
                    db.query(Message, MessageExtraDatum)
                    .join(
                        MessageExtraDatum,
                        and_(
                            MessageExtraDatum.message_id == Message.id,
                            MessageExtraDatum.user_id == member.user_id
                        )
                    ).filter(Message.id.in_(ids))
                )

            }
            for message, extra in message_map.values():
                if extra is None:
                    extra = MessageExtraDatum()
                    extra.message_id = message.id
                    extra.user_id = member.user_id
                extra.is_delete = True
                db.add(extra)
        db.commit()


        members_ids = [m.id for m in members]


        for item in members:

            unread_data = (
                db.query(func.min(Message.id), func.count(Message.id))
                    .join(
                        MessageExtraDatum,
                        and_(MessageExtraDatum.message_id == Message.id, MessageExtraDatum.user_id == item.user_id),
                        isouter=True
                    )
                    .filter(
                        Message.sender_id.in_(members_ids),
                        Message.sender_id != item.id,
                        not_(Message.is_delete),
                        or_(MessageExtraDatum.id == None, MessageExtraDatum.read == None),
                        or_(MessageExtraDatum.id == None, not_(MessageExtraDatum.is_delete)),
                    )
                    .first()
            )

            if unread_data is not None:
                first_message_id = unread_data[0]
                unread_count = unread_data[1]

            else:
                unread_count = 0
                first_message_id = None

            last_message_data = (
                db.query(func.max(Message.id))
                .join(
                    MessageExtraDatum,
                    and_(MessageExtraDatum.message_id == Message.id, MessageExtraDatum.user_id == item.user_id),
                    isouter=True
                )
                .filter(
                    Message.sender_id.in_(members_ids),
                    not_(Message.is_delete),
                    or_(MessageExtraDatum.id == None, not_(MessageExtraDatum.is_delete)),
                )
                .first()
            )

            if last_message_data is not None:
                last_message_id = last_message_data[0]
            else:
                last_message_id = None

            item.unread_count = unread_count
            item.first_message_id = first_message_id
            item.last_message_id = last_message_id

            db.add(item)

        db.commit()

    def get_service_chats(self, db: Session, user: User, subtypes: Optional[List[str]] = None, page: Optional[int] = None):


        query = (
            db.query(Chat)
            .join(Member, Member.chat_id == Chat.id)
            .filter(Chat.type_ == 'service')
            .filter(
                Member.is_tech,
                or_(Member.ended == None, Member.ended >= datetime.utcnow())
            )
        )
        query = query.distinct(Chat.id).order_by(Chat.id.desc())
        if subtypes is not None and len(subtypes) > 0:
            query = query.filter(Chat.subtype.in_(subtypes))

        data, paginator = get_page(query=query, page=page)

        return [
            get_chat_for_admin(datum, db, user)
            for datum
            in data
        ], paginator

    def get_messages_of_chat_for_admin(
            self,
            db: Session,
            chat_id: int,
            user: User,
            start_id: Optional[int] = None,
            limit: int = 30,
            mode: Optional[str] = None,
            sorting: Optional[str] = None,
            with_equals: Optional[bool] = None
    ):
        if with_equals is None:
            with_equals = True

        query = (
            db.query(Message)
            .join(Member, Message.sender_id == Member.id, isouter=True).filter(
                Member.chat_id == chat_id,

            )
        )

        if start_id is not None and mode == 'after':
            if with_equals:
                query = query.filter(Message.id >= start_id)
            else:
                query = query.filter(Message.id > start_id)
            query = query.order_by(Message.id)
        if start_id is not None and mode == 'before':
            if with_equals:
                query = query.filter(Message.id <= start_id)
            else:
                query = query.filter(Message.id < start_id)
            query = query.order_by(Message.id.desc())
        if limit is not None:
            query = query.limit(limit)

        messages = query.all()

        messages = sorted(messages, key=lambda message: message.created, reverse=sorting != 'old')

        return [
            get_message_with_parent(message, db, user) for message in messages
        ]

    def remove_user_data(self, db: Session, user_id: int):
        db.query(MessageExtraDatum).filter(MessageExtraDatum.user_id == user_id).delete()

        for m_chat in db.query(Chat).join(Member, Member.chat_id == Chat.id).filter(Member.user_id == user_id).all():
            for m_member in db.query(Member).filter(Member.chat_id == m_chat.id).all():
                m_member.first_message_id = None
                m_member.last_message_id = None
                db.add(m_member)
        db.commit()
        for m_chat in db.query(Chat).join(Member, Member.chat_id == Chat.id).filter(Member.user_id == user_id).all():
            for m_member in db.query(Member).filter(Member.chat_id == m_chat.id).all():
                db.delete(m_member)
            db.delete(m_chat)
        db.commit()



chat = CrudChat()
