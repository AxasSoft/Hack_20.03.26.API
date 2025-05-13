from typing import Optional, List

from pydantic import BaseModel, Field, validator

from .excursion_category import GettingExcursionCategory
from .excursion_review import GettingExcursionReview
from .id_model import IdModel
from ..enums.transfer_type import TransferType
from . import GettingUserShortInfo


class CreatingTransferRequest(BaseModel):
    type: TransferType
    passengers_quantity : int
    child_seat: bool = False
    animal: bool = False
    ski_supplies: bool = False
    comment: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "type": "economy",
                "passengers_quantity": 2,
                "ski_supplies": True,
                "comment": "comment",
            },
            "description": f"Статусы: {', '.join([f'{e.value} ({e.description})' for e in TransferType])}"
        }


class GettingTransfer(IdModel, CreatingTransferRequest):
    created: int
    user_id: int
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    tel: Optional[str]
