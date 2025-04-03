import enum
from typing import Optional

from pydantic import BaseModel, Field


class CreatingVerificationCode(BaseModel):
    tel: str = Field(...,title="Телефон")


class UpdatingVerificationCode(BaseModel):
    pass


class GettingVerificationCode(BaseModel):
    code: str


class VerifyingCode(BaseModel):
    tel: str = Field(...,title="Телефон")
    code: str = Field(...,title="Код подтверждения")