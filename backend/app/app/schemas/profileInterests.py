from typing import Optional

from pydantic import BaseModel, Field

from .id_model import IdModel
from .interest_dating import InterestsSubinterests

class ProfileInterestsBase(BaseModel):
    dating_profile_id: int
    interest_id: int

class ProfileInterests:
    interest_id: int
    interest: InterestsSubinterests