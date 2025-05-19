from pydantic import BaseModel

class GettingAudio(BaseModel):
    id: int
    link: str