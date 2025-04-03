from typing import Optional, List, Any

from pydantic import BaseModel, Field

from app.schemas.user import GettingUser


class GettingAttachment(BaseModel):
    id: int
    created: int
    link: str
    type: str


class GettingMessage(BaseModel):
    id: int
    created: int
    is_event: bool
    body: Optional[str]
    is_read_by_me: bool
    is_read_by_members: bool
    is_deleted: bool
    sender: GettingUser
    attachments: List[GettingAttachment]


class GettingMessageWithParent(GettingMessage):
    parent: Optional[Any]


class GettingChat(BaseModel):
    id: int
    type_: str = Field(..., alias='type')
    subtype: Optional[str]
    number: Optional[int]
    name: Optional[str]
    cover: Optional[str]
    member_count: int
    unread_count: int
    second_user: Optional[GettingUser]
    first_message_id: Optional[int]
    last_message: Optional[GettingMessageWithParent]


class NameBody(BaseModel):
    name: Optional[str]


class GettingMember(BaseModel):
    id: int
    created: int
    user: GettingUser


class CreatingMessage(BaseModel):
    body: Optional[str]
    attachment_ids: Optional[List[int]]


class CreatingMessageWithParent(CreatingMessage):
    parent_id: Optional[int]


class CreatingServiceChat(BaseModel):
    subtype: str
    first_message: Optional[CreatingMessage]


class CreatingGroupChat(BaseModel):
    chat_name: Optional[str]
    user_ids: Optional[List[int]]


class CreatingPersonalChat(BaseModel):
    user_id: int


class UpdatingGroupChat(BaseModel):
    chat_name: Optional[str]


class CreatingContacting(BaseModel):
    body: Optional[str]
    back_contacts: Optional[str]


class GettingContacting(BaseModel):
    id: int
    created: int
    body: Optional[str]
    back_contacts: Optional[str]
    processed: Optional[int]
    user: Optional[GettingUser]


class MembersBody(BaseModel):
    members: List[int]


class MessagesBody(BaseModel):
    messages: List[int]






