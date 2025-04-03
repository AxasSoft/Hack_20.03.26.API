from pydantic import BaseModel

class GettingImage(BaseModel):
    id: int
    link: str