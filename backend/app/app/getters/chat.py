from typing import Optional

from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import Session

from app.getters import get_user_short_info
from app.getters.timestamp import to_timestamp
from app.models import Chat, Attachment, Message, User, Member, DeletedMessage
from app.schemas import GettingChat, GettingAttachment, GettingMessage, GettingMessageWithParent, GettingCoutnUnRead


def get_attachment(attachment: Attachment) -> GettingAttachment:
    return GettingAttachment(
        id=attachment.id,
        link=attachment.link,
        note=attachment.note
    )


def get_message(db: Session, message: Message, current_user: Optional[User]) -> GettingMessage:
    result =  GettingMessage(
        id=message.id,
        created=to_timestamp(message.created),
        sender=get_user_short_info(db_obj=message.sender.user),
        text=message.text,
        is_read=bool(message.is_read),
        attachments=[
            get_attachment(attachment=attachment) for attachment in message.attachments
        ]
    )

    return result

def get_message_with_parent(message, db, user):
    result = GettingMessageWithParent(
        # **get_message(message=message, db=db, current_user=user).dict(),
        id=message.id,
        created=to_timestamp(message.created),
        sender=get_user_short_info(db_obj=message.sender.user),
        text=message.text,
        is_read=bool(message.is_read),
        attachments=[
            get_attachment(attachment=attachment) for attachment in message.attachments
        ],
        parent=get_message(message=message.parent, db=db, current_user=None) if message.parent is not None else None
    )
    return result


def get_chat(db: Session, chat: Chat, current_user: User) -> GettingChat:
    recipient: Member = chat.recipient
    initiator: Member = chat.initiator
    if recipient.user == current_user:
        current_member = recipient
        second_member = initiator
    else:
        current_member = initiator
        second_member = recipient

    last_message = current_member.last_message
    if last_message is None:
        delete_before_id = current_member.delete_before_id

        query =  db.query(Message) \
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

        query = query.order_by(desc(Message.created))

        last_message = query.first()

    count_unread_messages = db.query(func.count(Message.id)) \
        .filter(
            Message.sender_id.in_((recipient.id, initiator.id)),
            Message.is_read == False,
            Message.sender_id != current_member.id
        ).scalar()

    quantity_messages = db.query(func.count(Message.id)) \
        .filter(Message.sender_id.in_((recipient.id, initiator.id))) \
        .scalar()

    result = GettingChat(
            id=chat.id,
            count_unread_messages=count_unread_messages if count_unread_messages else 0,
            quantity_messages=quantity_messages if quantity_messages else 0,
            type_chat=chat.type_chat if chat.type_chat else None,
            user=get_user_short_info(second_member.user),
            last_message=get_message(
                db=db,
                message=last_message,
                current_user=current_user
            ) if last_message is not None else None,
            is_blocked = current_member.is_blocked if current_member.is_blocked else False,
            is_blocker = current_member.is_blocker if current_member.is_blocked else False
        )

    if result.type_chat is not None:
        result.type_chat = result.type_chat.value
    return result

def get_unread_messages_count(obj: int) -> GettingCoutnUnRead:
    return GettingCoutnUnRead(
        count=obj
    )