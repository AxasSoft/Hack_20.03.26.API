import enum
from typing import List, Optional

from app.schemas.profile_avatar import ProfileAvatarBase
from app.schemas.user import Gender, GettingUser
from pydantic import BaseModel, EmailStr, Field

from .facts import FactsSubFacts
from .genre_music_dating import GenreMusicSubGenreMusic
from .id_model import IdModel
from .interest_dating import InterestsSubinterests
from app.enums.relationship_type_dating import RelationshipType


class DatingProfileBase(BaseModel):
    films: Optional[str]
    book: Optional[str]
    about: Optional[str]
    education: Optional[str]
    work: Optional[str]
    relationship_type: Optional[RelationshipType]


class CreatingUpdatingDatingBase(DatingProfileBase):
    sub_interest_id: Optional[List[int]]
    sub_facts_id: Optional[List[int]]
    sub_genre_music_id: Optional[List[int]]


class CreatingDatingProfile(CreatingUpdatingDatingBase):
    pass


class UpdatingDatingProfile(CreatingUpdatingDatingBase):
    pass


class LikeDisLikeDatingProfile(BaseModel):
    profile_id: int
    like: bool
    liker_estimate_type: int = Field(None, ge=0, le=4)


class GettingDatingProfile(DatingProfileBase):
    id: int
    avatar_urls: Optional[List[ProfileAvatarBase]]
    profile_interests: Optional[List[InterestsSubinterests]]
    profile_facts: Optional[List[FactsSubFacts]]
    profile_genre_music: Optional[List[GenreMusicSubGenreMusic]]
    user: Optional[GettingUser]


class GettingDatingProfileLike(BaseModel):
    id: int
    liker_dating_profile: Optional[GettingDatingProfile]
    liked_dating_profile: Optional[int]
    # liked_dating_profile: Optional[GettingDatingProfile]

class GettingDatingProfileMutual(BaseModel):
    id: int
    liker_dating_profile: Optional[GettingDatingProfile]
    liked_dating_profile: Optional[GettingDatingProfile]
    mutual: Optional[bool]