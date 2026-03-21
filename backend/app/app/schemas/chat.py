import enum
from typing import Optional, List, Any

from app.schemas import GettingUserShortInfo
from pydantic import BaseModel, EmailStr, Field
from app.enums.type_chat import TypeChat

from .id_model import IdModel


class GettingAttachment(IdModel, BaseModel):
    link: str
    note: Optional[str]


class GettingMessage(IdModel, BaseModel):
    created: Optional[int]
    sender: Optional[GettingUserShortInfo]
    text: Optional[str]
    is_read: bool
    attachments: List[GettingAttachment]

class GettingMessageWithParent(GettingMessage):
    parent: Optional[Any]

class SendingMessage(BaseModel):
    text: Optional[str]
    attachments: List[int]

class CreatingMessageWithParent(SendingMessage):
    parent_id: Optional[int]

class GettingChat(IdModel, BaseModel):
    type_chat: Optional[TypeChat]
    count_unread_messages: Optional[int]
    quantity_messages: Optional[int]
    user: Optional[GettingUserShortInfo]
    last_message: Optional[GettingMessage]
    is_blocked: bool
    is_blocker: bool


class OrderBy(enum.Enum):
    asc = "asc"
    desc = "desc"

class MessagesList(BaseModel):
    messages: Optional[List[int]]

class GettingCoutnUnRead(BaseModel):
    count: Optional[int]
