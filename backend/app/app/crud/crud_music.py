from app.crud.base import CRUDBase
from app.models import Music
from app.schemas import CreatingMusic, UpdatingMusic


class CRUDMusic(CRUDBase[Music, CreatingMusic, UpdatingMusic]):
    pass


music = CRUDMusic(Music)