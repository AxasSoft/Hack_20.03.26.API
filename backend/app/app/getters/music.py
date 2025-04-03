from app.models import Music
from app.schemas import GettingMusic


def get_music(music: Music) -> GettingMusic:
    return GettingMusic(
        id=music.id,
        name=music.name
    )