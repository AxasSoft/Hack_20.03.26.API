from typing import Optional, List, Dict
from .sub_interest import  Subinterest
from pydantic import BaseModel, Field

from .id_model import IdModel


class ProfileAvatarBase(BaseModel):
    id: int 
    url: str
