from app.models import Facts, ProfileFacts
from app.schemas import GettingSubFacts


def get_sub_facts(obj: Facts) -> GettingSubFacts:
    return GettingSubFacts(
        id=obj.id,
        sub_facts_name=obj.facts_name,
        parent_facts=obj.parent_facts_id
    )


# def add_sub_interest_dating_profile(sub_interest: ProfileInterests) -> ProfileInterestsBase:
#     return ProfileInterestsBase(
#         dating_profile_id=sub_interest.dating_profile_id,
#         interest_id=sub_interest.interest_id
#     )