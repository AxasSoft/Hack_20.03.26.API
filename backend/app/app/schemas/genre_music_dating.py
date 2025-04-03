from typing import Optional, List, Dict
from .sub_genre_music import  SubGenreMusic
from pydantic import BaseModel, Field

from .id_model import IdModel

class GenreMusicBase(BaseModel):
    genre_music_name: Optional[str]


class CreatingGenreMusic(GenreMusicBase):
    pass 


class UpdatingGenreMusic(GenreMusicBase):
    pass


class GettingGenreMusic(IdModel, GenreMusicBase):
    pass


class GenreMusicSubGenreMusic(BaseModel):
    genre_music_id: int
    genre_music_name: str
    sub_genre_music: List[SubGenreMusic]