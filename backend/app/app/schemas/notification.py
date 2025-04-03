from typing import Optional

from pydantic import BaseModel, Field

from app.schemas import GettingUser


class GettingNotification(BaseModel):
    id: int
    icon: Optional[str]
    title: Optional[str]
    body: Optional[str]
    created: Optional[int]
    link: Optional[str]
    order_id: Optional[int]
    offer_id: Optional[int]
    stage: Optional[int]
    is_read: bool = Field(False)
    has_feedback_about_me: bool = Field(False)
    user: Optional[GettingUser]
    second_user: Optional[GettingUser]
    order_name: Optional[str]


class IsReadBody(BaseModel):
    is_read: bool