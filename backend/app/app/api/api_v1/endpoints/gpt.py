from fastapi import APIRouter, Depends, Query

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from app.services.free4gpt.gpt_manager import gpt_manager

router = APIRouter()


@router.post(
    "/answer_gpt/",
    response_model=schemas.SingleEntityResponse[schemas.ChatGPTAnswer],
    name="Задать вопрос ИИ",
    tags=["Мобильное приложение / ГПТ"],

)
def get_answer(
    question: schemas.GPTQuestionRequest,
):
    answer = gpt_manager.get_answer(question=question.text)
    print(answer)
    return schemas.SingleEntityResponse(
        data=schemas.ChatGPTAnswer(answer=answer)
    )