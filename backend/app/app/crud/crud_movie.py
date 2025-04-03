from app.crud.base import CRUDBase
from app.models import Movie
from app.schemas import CreatingMovie, UpdatingMovie


class CRUDMovie(CRUDBase[Movie, CreatingMovie, UpdatingMovie]):
    pass


movie = CRUDMovie(Movie)