import datetime
import logging
from typing import Any, Dict, Optional, Union, Type, List, Tuple
import os
import uuid
from app.utils import pagination
from botocore.client import BaseClient
from fastapi import UploadFile
from sqlalchemy import cast, String, or_, not_, and_, func, desc, alias, asc
from sqlalchemy.orm import Session, aliased
from app.enums.type_chat import TypeChat
from botocore.exceptions import NoCredentialsError, ClientError

from app.models.user import User

from ..models import Chat, Member, Message, DeletedMessage, Attachment
from ..schemas import SendingMessage, OrderBy
from ..exceptions import InaccessibleEntity



class CrudChat:

    def __init__(self, s3_bucket_name: Optional[str], s3_client: Optional[BaseClient]):
        self.s3_bucket_name = s3_bucket_name
        self.s3_client = s3_client

    def _last_message_of_chat(self, db:Session, chat: Chat, member: Member):
        query = db.query(Message) \
            .join(
                DeletedMessage,
                and_(DeletedMessage.message_id == Message.id, DeletedMessage.member_id == chat.initiator.id),
                isouter=True
            ) \
            .filter(
                Message.sender_id.in_(
                    (chat.recipient.id, chat.initiator.id,)
                ),
                DeletedMessage.id == None
            )

        delete_before_id = member.delete_before_id
        if delete_before_id is not None:
            query = query.filter(Message.id > delete_before_id)

        query = query.order_by(desc(Message.created))

        last_message = query.first()

        return last_message
    
    def _get_all_active_chat(self, db:Session, current_user: User, type_chat: Optional[int]):
        Member1 = alias(Member)
        Member2 = alias(Member)

        active_members_subquery  = db.query(Member.id).filter(
            Member.user_id == current_user.id,
            Member.ended == None 
        ).subquery()

        query = (
            db.query(Chat)
                .join(Member1, Chat.initiator_id == Member1.c.id)
                .join(Member2, Chat.recipient_id == Member2.c.id)
                .join(
                Message,
                or_(
                    and_(Member1.c.user_id == current_user.id, Member1.c.last_message_id == Message.id),
                    and_(Member2.c.user_id == current_user.id, Member2.c.last_message_id == Message.id)
                ),
                isouter=True
            )
                .filter(or_(Member1.c.user_id == current_user.id, Member2.c.user_id == current_user.id)) \
                .filter(or_(Member1.c.id.in_(active_members_subquery), Member2.c.id.in_(active_members_subquery)))  # Фильтрация по полю ended
                .order_by(desc(Message.created))
        )

        if type_chat is not None:
            type_chat_str = TypeChat(type_chat).name
            query = query.filter(
                and_(Chat.type_chat == type_chat_str, Chat.type_chat != None)
                )
            
        all_chat = query.all()
        return all_chat

    
     # Обновление статуса участников чата
    def _update_member_status(self, db: Session, user_id: int , chat: Chat):
        member = db.query(Member)\
            .filter(
                Member.user_id == user_id,
                or_(
                    Member.initiated_chat.has(Chat.id == chat.id),
                    Member.received_chat.has(Chat.id == chat.id)
                )
            ).first()
        if member and member.ended is not None:
            member.started = datetime.datetime.utcnow()
            member.ended = None
            db.add(member)
            db.commit()
            db.refresh(member)
    
    def find_member(self, db: Session, chat_id: int, user: User):
        
        member_subquery = db.query(Member.id).filter(
            Member.user_id == user.id,
            or_(
                Member.initiated_chat.has(Chat.id == chat_id),
                Member.received_chat.has(Chat.id == chat_id)
            )
        ).subquery()

        return db.query(Member) \
            .filter(Member.id.in_(member_subquery)) \
            .first()
    
    def remove_members(self, db: Session, member: Member):
        if member:
            member.ended = datetime.datetime.utcnow()
            member.first_message_id = None
            member.last_message_id = None
            db.add(member)

    def get_chat_by_id(self, db: Session, id: int):
        return db.query(Chat).get(id)

    def get_message_by_id(self, db: Session, id: int):
        return db.query(Message).get(id)

    def get_attachment_by_id(self, db: Session, id: int):
        return db.query(Attachment).get(id)

    def get_active_chats(
            self,
            db: Session,
            current_user: User,
            page: Optional[int],
            type_chat: Optional[int],
            is_empty_chat: Optional[bool]
    ):
        Member1 = alias(Member)
        Member2 = alias(Member)

        active_members_subquery = (
            db.query(Member.id)
            .filter(
                Member.user_id == current_user.id,
                Member.ended == None
            )
            .subquery()
        )

        query = (
            db.query(Chat)
            .join(Member1, Chat.initiator_id == Member1.c.id)
            .outerjoin(Member2, Chat.recipient_id == Member2.c.id)  # FIX
            .outerjoin(
                Message,
                or_(
                    and_(
                        Member1.c.user_id == current_user.id,
                        Member1.c.last_message_id == Message.id
                    ),
                    and_(
                        Member2.c.user_id == current_user.id,
                        Member2.c.last_message_id == Message.id
                    )
                )
            )
            .filter(
                or_(
                    Member1.c.user_id == current_user.id,
                    Member2.c.user_id == current_user.id
                )
            )
            .filter(
                or_(
                    Member1.c.id.in_(active_members_subquery),
                    Member2.c.id.in_(active_members_subquery)
                )
            )
            .order_by(desc(Message.created))
        )

        if type_chat is not None:
            type_chat_str = TypeChat(type_chat).name
            query = query.filter(Chat.type_chat == type_chat_str)

        if is_empty_chat is False:
            query = query.filter(
                or_(
                    Member1.c.last_message_id != None,
                    Member2.c.last_message_id != None
                )
            )

        return pagination.get_page(query, page)


        return pagination.get_page(
            query,
            page
        )
    
    def get_unread_messages_count(self, db: Session, current_user: User, type_chat: int):
        all_user_chat = self._get_all_active_chat(db=db, current_user=current_user, type_chat=type_chat)
        print(f'-=-=-=-=-=-={all_user_chat}')
        unread_messages_count = 0
        for chat in all_user_chat:
            recipient: Member = chat.recipient
            initiator: Member = chat.initiator
            if recipient.user == current_user:
                current_member = recipient
                second_member = initiator
            else:
                current_member = initiator
                second_member = recipient

            unread_messages_count += (db.query(func.count(Message.id)) \
            .filter(
                Message.sender_id.in_((recipient.id, initiator.id)),
                Message.is_read == False,
                Message.sender_id != current_member.id
            ).scalar())
            print(f"{unread_messages_count}")

        print("Unread messages count:", unread_messages_count)

        return unread_messages_count

    def init_chat(self, db: Session, initiator: User, recipient: Optional[User], type_chat: int):
        created = False
        logging.info(f"initiator={initiator}")
        logging.info(f"recipient={recipient}")

        Member1 = alias(Member)
        Member2 = alias(Member)

        type_chat_str = TypeChat(type_chat).name if type_chat is not None else None
        if type_chat == 3:
            chat = db.query(Chat) \
                .join(Member1, Chat.initiator_id == Member1.c.id) \
                .filter(
                    and_(
                        Member1.c.user_id == initiator.id,
                        Chat.type_chat == type_chat_str,
                    )
                ) \
                .first()
        else:
            chat = db.query(Chat) \
                .join(Member1, Chat.recipient_id == Member1.c.id) \
                .join(Member2, Chat.initiator_id == Member2.c.id) \
                .filter(
                    or_(
                        and_(Member1.c.user_id == recipient.id, Member2.c.user_id == initiator.id),
                        and_(Member2.c.user_id == recipient.id, Member1.c.user_id == initiator.id),
                    ),
                    Chat.type_chat == type_chat_str
                ) \
                .first()

        if chat is None:
            created = True
            initiator_member = Member()
            initiator_member.user = initiator
            initiator_member.started = datetime.datetime.utcnow()
            db.add(initiator_member)
            recipient_member = None
            if recipient:
                recipient_member = Member()
                recipient_member.user = recipient
                recipient_member.started = datetime.datetime.utcnow()
                db.add(recipient_member)
            chat = Chat()
            chat.recipient = recipient_member if recipient_member else None
            chat.initiator = initiator_member
            if type_chat is not None:
                type_chat_str = TypeChat(type_chat)
                chat.type_chat = type_chat_str
            db.add(chat)
            db.commit()

        self._update_member_status(db=db, user_id=initiator.id, chat=chat)
        
        # member_subquery = db.query(Member.id).filter(
        #     Member.user_id == initiator.id,
        #     or_(
        #         Member.initiated_chat.has(Chat.id == chat.id),
        #         Member.received_chat.has(Chat.id == chat.id)
        #     )
        # ).subquery()
        # current_member = db.query(Member) \
        #     .filter(Member.id.in_(member_subquery)) \
        #     .first()
        # if current_member is not None and current_member.ended is not None:
        #     current_member.started = datetime.datetime.utcnow()
        #     current_member.ended = None
        #     db.add(current_member)

        # member_subquery = db.query(Member.id).filter(
        #     Member.user_id == recipient.id,
        #     or_(
        #         Member.initiated_chat.has(Chat.id == chat.id),
        #         Member.received_chat.has(Chat.id == chat.id)
        #     )
        # ).subquery()
        # second_member = db.query(Member) \
        #     .filter(Member.id.in_(member_subquery)) \
        #     .first()
        # if second_member is not None and second_member.ended is not None:
        #     second_member.started = datetime.datetime.utcnow()
        #     second_member.ended = None
        #     db.add(second_member)
        # db.commit()

        return chat, created

    def get_messages(
        self,
        db: Session,
        current_user: User,
        chat: Chat,
        timestamp: datetime.datetime,
        count: int,
        order_by: Optional[str] = None,
        with_equal: bool = False,
        start_id: Optional[int] = None,  # Добавляем параметр start_id
        mode: Optional[str] = None,
):      
        if with_equal is None:
            with_equal = True
        if mode is None:
            mode = 'before'
        recipient: Member = chat.recipient
        initiator: Member = chat.initiator
        if recipient.user == current_user:
            current_member = recipient
        elif initiator.user == current_user:
            current_member = initiator
        else:
            return []

        delete_before_id = current_member.delete_before_id

        query = db.query(Message) \
            .join(
                DeletedMessage,
                and_(DeletedMessage.message_id == Message.id, DeletedMessage.member_id == current_member.id),
                isouter=True
            ) \
            .filter(
                Message.sender_id.in_(
                    (recipient.id, initiator.id,)
                ),
                DeletedMessage.id == None
            )

        if delete_before_id is not None:
            query = query.filter(Message.id > delete_before_id)

        if start_id is not None and mode == 'after':
            if with_equal:
                query = query.filter(Message.id >= start_id)
            else:
                query = query.filter(Message.id > start_id)
            query = query.order_by(Message.id)
        if start_id is not None and mode == 'before':
            if with_equal:
                query = query.filter(Message.id <= start_id)
            else:
                query = query.filter(Message.id < start_id)

        if order_by == 'asc':
            query = query.order_by(asc(Message.created))
        else:
            query = query.order_by(desc(Message.created))

        if count == 0:
            return query.all()
        elif count > 0 and with_equal:
            query = query.filter(Message.created > timestamp + datetime.timedelta(seconds=1)).limit(count)
        elif count > 0 and not with_equal:
            query = query.filter(Message.created > timestamp).limit(count)
        elif count < 0 and with_equal:
            query = query.filter(Message.created < timestamp + datetime.timedelta(seconds=1)).limit(-count)
        elif count < 0 and not with_equal:
            query = query.filter(Message.created < timestamp).limit(-count)
        
        

        # return sorted(
        #     query,
        #     key=lambda msg: msg.created,
        #     reverse = order_by == OrderBy.desc
        # )

        return query

    def delete_messages(self, db: Session, chat: Chat, current_user: User, for_all: bool = False):
        recipient: Member = chat.recipient
        initiator: Member = chat.initiator
        if recipient.user == current_user:
            current_member = recipient
        elif initiator.user == current_user:
            current_member = initiator
        else:
            return None

        if for_all:
            members = (recipient, initiator,)
        else:
            members = (current_member,)

        for member in members:

            member.delete_before_id = member.last_message_id
            db.add(member)
            db.commit()

            last_message = self._last_message_of_chat(db, chat, member)
            member.last_message = last_message
            db.add(member)
            db.commit()

    def delete_message(self, db: Session, message: Message, current_user: User, for_all: bool = False):

        chat = message.sender.initiated_chat or message.sender.received_chat

        recipient: Member = chat.recipient
        initiator: Member = chat.initiator
        if recipient.user == current_user:
            current_member = recipient
        elif initiator.user == current_user:
            current_member = initiator
        else:
            return None

        if for_all:
            members = (recipient, initiator)
        else:
            members = (current_member,)

        for member in members:
            deleted = DeletedMessage()
            deleted.member = member
            deleted.message = message
            db.add(deleted)
            member.last_message = self._last_message_of_chat(db, chat, member)
            db.add(member)
            db.commit()

        return None

    def load_attachment(self, db: Session, current_user: User, attachment: UploadFile, note: str):
        bucket_name = self.s3_bucket_name
        host = self.s3_client._endpoint.host
        url_prefix = host + '/' + bucket_name + '/'

        short_name = uuid.uuid4().hex + os.path.splitext(attachment.filename)[1]
        name = 'stories/attachments/'+short_name
        new_url = url_prefix + name

        input_body=attachment.file.read()

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=input_body,
            ContentType=attachment.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        attachment = Attachment()
        attachment.link = new_url
        attachment.note = note

        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        return attachment
    
    def delete_attachment(self, db: Session, attachment: Attachment) -> bool:
        bucket_name = self.s3_bucket_name
        host = self.s3_client._endpoint.host
        url_prefix = host + '/' + bucket_name + '/'

        if attachment is not None and attachment.link.startswith(url_prefix):
            key = attachment.link[len(url_prefix):]
        else:
            return False

        try:
            response = self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=key
            )
            if not (200 <= response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
                return False

            db.delete(attachment)
            db.commit()

            return True
        except (NoCredentialsError, ClientError) as e:
            return False

    def send_message(self, db: Session, current_user: User, chat: Chat, message: SendingMessage):
        member = db.query(Member)\
            .filter(
                Member.user_id == current_user.id,
                or_(Member.initiated_chat == chat, Member.received_chat == chat)
            )\
            .first()
        if member is None:
            return None
        if member.is_blocker:
            raise InaccessibleEntity('Вы заблокировали этого пользователя')
        if member.is_blocked:
            raise InaccessibleEntity('Пользователь вас заблокировал')

        db_message = Message()
        db_message.sender = member
        db_message.text = message.text
        db_message.parent_id = message.parent_id if message.parent_id else None
        db.add(db_message)
        for attachment_id in message.attachments:
            db_attachment: Optional[Attachment] = db.query(Attachment).get(attachment_id)
            if db_attachment is None:
                continue
            if db_attachment.message is not None:
                continue
            db_attachment.message = db_message
            db.add(db_attachment)
        db.commit()

        if chat.initiator:
            chat.initiator.last_message = db_message
            db.add(chat.initiator)
        if chat.recipient:
            chat.recipient.last_message = db_message
            db.add(chat.recipient)

        db.commit()

        if chat.initiator:
            self._update_member_status(db=db, user_id=chat.initiator.user_id, chat=chat)
        if chat.recipient:
            self._update_member_status(db=db, user_id=chat.recipient.user_id, chat=chat)

        return db_message


    def mark_read(self, db: Session, message_ids: List[int]):
        for message in db.query(Message).filter(Message.id.in_(message_ids)):
            message.is_read = True
            db.add(message)
        db.commit()

    def block_user(self, db: Session, current_user: User, chat: Chat, second_user: User, blocking: bool):
        current_member = db.query(Member)\
            .filter(
                Member.user_id == current_user.id,
                or_(Member.initiated_chat == chat, Member.received_chat == chat)
            )\
            .first()
        second_member = db.query(Member)\
            .filter(
                Member.user_id == second_user.id,
                or_(Member.initiated_chat == chat, Member.received_chat == chat)
            )\
            .first()
        if blocking:
            if current_member.is_blocker and second_member.is_blocked:
                return chat

            else:
                current_member.is_blocker = True
                second_member.is_blocked = True
        else:
            if not current_member.is_blocker and not second_member.is_blocked:
                return chat

            else:
                current_member.is_blocker = False
                second_member.is_blocked = False

        db.commit()
        db.refresh(chat)
        return chat


