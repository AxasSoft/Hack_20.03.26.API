from app.models import GenreMusic
from app.schemas import GettingGenreMusic
from typing import List, Optional

def get_genre_music(obj: GenreMusic) -> GettingGenreMusic:
    return GettingGenreMusic(
        id=obj.id,
        genre_music_name=obj.genre_music_name
    )

