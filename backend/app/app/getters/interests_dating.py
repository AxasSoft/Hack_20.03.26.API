from app.models import Interests
from app.schemas import GettingInterest, ListOfEntityResponse
from typing import List, Optional

def get_interest(interest: Interests) -> GettingInterest:
    return GettingInterest(
        id=interest.id,
        interest_name=interest.interest_name
    )

