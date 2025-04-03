from app.models import Facts
from app.schemas import GettingFacts
from typing import List, Optional

def get_facts(facts: Facts) -> GettingFacts:
    return GettingFacts(
        id=facts.id,
        facts_name=facts.facts_name
    )

