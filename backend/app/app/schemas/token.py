from typing import Optional

from pydantic import BaseModel

from app.schemas import GettingUser


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


class TokenWithUser(BaseModel):
    access_token: str
    user: GettingUser
