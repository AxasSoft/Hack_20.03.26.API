from app.models import Page
from app.schemas import GettingPage


def get_page(page: Page) -> GettingPage:
    return GettingPage(
        id=page.id,
        tech_name=page.tech_name,
        title=page.title,
        body=page.body
    )
