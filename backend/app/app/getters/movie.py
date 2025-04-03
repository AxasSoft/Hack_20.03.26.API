from app.models import Movie
from app.schemas import GettingMovie


def get_movie(movie: Movie) -> GettingMovie:
    return GettingMovie(
        id=movie.id,
        name=movie.name
    )