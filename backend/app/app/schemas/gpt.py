from pydantic import BaseModel, Field


class ChatGPTAnswer(BaseModel):
    answer: str


class GPTQuestionRequest(BaseModel):
    text: str