from typing import Optional, List

from pydantic import BaseModel, Field, validator

from .excursion_category import GettingExcursionCategory
from .excursion_review import GettingExcursionReview
from .id_model import IdModel
from ..enums.transfer_type import TransferType


class CreatingTransferRequest(BaseModel):
    type: TransferType
    passengers_quantity : int
    child_seat: bool = False
    animal: bool = False
    ski_supplies: bool = False


