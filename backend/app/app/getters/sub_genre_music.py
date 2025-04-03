from app.models import GenreMusic, ProfileGenreMusic
from app.schemas import GettingSubGenreMusic


def get_sub_genre_music(obj: GenreMusic) -> GettingSubGenreMusic:
    return GettingSubGenreMusic(
        id=obj.id,
        sub_genre_music_name=obj.genre_music_name,
        parent_genre_music=obj.parent_genre_music_id
    )


# def add_sub_interest_dating_profile(sub_interest: ProfileInterests) -> ProfileInterestsBase:
#     return ProfileInterestsBase(
#         dating_profile_id=sub_interest.dating_profile_id,
#         interest_id=sub_interest.interest_id
#     )