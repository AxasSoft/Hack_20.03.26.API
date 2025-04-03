
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.order import GettingOrder

from app.schemas.info import GettingInfo

from app.schemas.subcategory import GettingSubcategory



class CreatingPromoOrder(BaseModel):
    link: Optional[str] = None
    order_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    info_id: Optional[int] = None


class UpdatingPromoOrder(CreatingPromoOrder):
    pass


class GettingPromoOrder(BaseModel):
    id: int
    created: Optional[int] = None 
    cover: Optional[str] = None
    link: Optional[str] = None
    order: Optional[GettingOrder] = None
    subcategory: Optional[GettingSubcategory] = None
    info: Optional[GettingInfo] = None

