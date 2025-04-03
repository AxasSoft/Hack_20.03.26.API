from typing import Optional, List

from pydantic import BaseModel

from .id_model import IdModel

class SubGenreMusicBase(BaseModel):
    genre_music_name: Optional[str]

class CreatingSubGenreMusic(SubGenreMusicBase):
    parent_genre_music_id: int

class UpdatingSubGenreMusic(SubGenreMusicBase):
    pass

class GettingSubGenreMusic(IdModel, BaseModel):
    id: Optional[int]
    sub_genre_music_name: str
    parent_genre_music: Optional[int]
    
class AddUserProfilSubGenreMusic(BaseModel):
    id: List[int]

class SubGenreMusic(BaseModel):
    sub_genre_music_id: int
    sub_genre_music_name: str
