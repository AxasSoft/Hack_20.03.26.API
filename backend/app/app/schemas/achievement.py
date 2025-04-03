from typing import Optional

from pydantic import BaseModel


class CreatingAchievement(BaseModel):
    name: str
    description: Optional[str] = None
    counter: int
    reward: int


class UpdatingAchievement(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    counter: Optional[int] = None
    reward: Optional[int] = None


class GettingAchievement(BaseModel):
    id: int
    created: int
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None
    counter: int
    reward: int


class GettingUserAchievement(GettingAchievement):
    completed: bool
