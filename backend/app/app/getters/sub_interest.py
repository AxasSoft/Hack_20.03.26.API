from app.models import Interests, ProfileInterests
from app.schemas import GettingSubInterest, ProfileInterestsBase


def get_sub_interest(sub_interest: Interests) -> GettingSubInterest:
    return GettingSubInterest(
        id=sub_interest.id,
        subinterest_name=sub_interest.interest_name,
        parent_interest=sub_interest.parent_interest_id
    )


def add_sub_interest_dating_profile(sub_interest: ProfileInterests) -> ProfileInterestsBase:
    return ProfileInterestsBase(
        dating_profile_id=sub_interest.dating_profile_id,
        interest_id=sub_interest.interest_id
    )