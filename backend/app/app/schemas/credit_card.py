import enum
from typing import Optional, List

from app.schemas import GettingUserShortInfo
from pydantic import BaseModel, EmailStr, Field

from .id_model import IdModel


class CreditCardData(BaseModel):
    card_number: str
    year: str
    month: str
    card_holder: str


class CreditCardCvc(BaseModel):
    cvc: Optional[str]