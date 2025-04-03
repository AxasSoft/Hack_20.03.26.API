from app.models.interest_user import Interest
from app.schemas.interest_user import GettingInterestUser


def get_interest_user(interest: Interest) -> GettingInterestUser:
    return GettingInterestUser(
        id=interest.id,
        name=interest.name
    )