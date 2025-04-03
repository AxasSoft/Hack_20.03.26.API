from app.models import Achievement
from app.schemas.achievement import GettingAchievement
from app.utils.datetime import to_unix_timestamp


def get_achievement(achievement: Achievement) -> GettingAchievement:
    return GettingAchievement(
        id=achievement.id,
        created=to_unix_timestamp(achievement.created),
        name=achievement.name,
        description=achievement.description,
        cover=achievement.cover,
        counter=achievement.counter,
        reward=achievement.reward,
    )
