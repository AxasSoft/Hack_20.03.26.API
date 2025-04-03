from typing import Optional, List, Dict
from .sub_facts import SubFacts
from pydantic import BaseModel, Field, conint
from app.schemas.user import GettingUserShortInfo
from app.schemas.order import GettingOrder
from .id_model import IdModel

class BaseFeedbackOrder(BaseModel):
    title: Optional[str] = None 
    text: Optional[str] = None 
    rate: Optional[conint(ge=1, le=5)] = None 

class CreatingFeedbackOrder(BaseFeedbackOrder):
    pass 

class UpdatingFeedbackOrder(BaseFeedbackOrder):
    pass

class GettingFeedbackOrder(BaseFeedbackOrder):
    id: int
    created: int
    updated: Optional[int] 
    creator: Optional[GettingUserShortInfo]
    order: Optional[GettingOrder]
    owner_order: Optional[GettingUserShortInfo]

