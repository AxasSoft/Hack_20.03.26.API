from app import crud, getters, models, schemas
from app.api import deps
from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    "/cp/subfacts/",
    tags=["Административная панель / Подфакты Знакомства"],
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubFacts],
    name="Получить все доступные подфакты",
)
@router.get(
    "/subfacts/",
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubFacts],
    name="Получить все доступные подфакты",
    tags=["Мобильное приложение / Подфакты Знакомства"],
)
def get_all(
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
):
    sub_facts, total = crud.sub_facts.get_sub_fucts(db=db)
    return schemas.ListOfEntityResponse(
        data=[getters.sub_facts.get_sub_facts(sub_fact) for sub_fact in sub_facts]
    )


@router.get(
    "/subfacts/user",
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubFacts],
    name="Получить все доступные подфакты текущего пользователя",
    tags=["Мобильное приложение / Подфакты Знакомства"],
)
def get_all_user(
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
):
    if current_user.is_dating_profile is False:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
    sub_facts = crud.sub_facts.get_sub_fucts_current_user(db=db, user=current_user)
    return schemas.ListOfEntityResponse(
        data=[getters.sub_facts.get_sub_facts(sub_fact) for sub_fact in sub_facts]
    )


@router.post(
    "/cp/subfacts/",
    response_model=schemas.SingleEntityResponse[schemas.GettingSubFacts],
    name="Добавить подфакт",
    description="Добавить новый подфакт",
    responses={
        400: {
            "model": schemas.OkResponse,
            "description": "Переданны невалидные данные",
        },
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
        403: {"model": schemas.OkResponse, "description": "Отказанно в доступе"},
    },
    tags=["Административная панель / Подфакты Знакомства"],
)
def create_sub_interest(
    data: schemas.CreatingSubFacts,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    facts = crud.facts.get_by_id(db, data.parent_facts_id)
    if facts is None:
        raise UnfoundEntity(message="Факт не найден")

    sub_facts = crud.sub_facts.create_sub_fucts(db, obj_in=data)

    return schemas.SingleEntityResponse(data=getters.sub_facts.get_sub_facts(sub_facts))


@router.put(
    "/cp/subfacts/{sub_facts_id}/",
    response_model=schemas.SingleEntityResponse[schemas.GettingSubFacts],
    name="Изменить подфакт",
    description="Изменить подфакт",
    responses={
        400: {"model": schemas.OkResponse, "description": "Переданы невалидные данные"},
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
        403: {"model": schemas.OkResponse, "description": "Отказано в доступе"},
        404: {"model": schemas.OkResponse, "description": "Категория не найдена"},
    },
    tags=["Административная панель / Подфакты Знакомства"],
)
def edit_interest(
    data: schemas.UpdatingSubFacts,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    sub_facts_id: int = Path(..., description="Идентификатор подфакт"),
):
    sub_fact = crud.sub_facts.get_by_id(db, sub_facts_id)
    if sub_fact is None:
        raise UnfoundEntity(message="Подфакт не найден")
    new_sub_fact = crud.sub_facts.update(db, db_obj=sub_fact, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.sub_facts.get_sub_facts(new_sub_fact)
    )


@router.delete(
    "/cp/subfacts/{sub_facts_id}/",
    response_model=schemas.OkResponse,
    name="Удалить подфакт",
    description="Удалить подфакт",
    responses={
        400: {
            "model": schemas.OkResponse,
            "description": "Переданны невалидные данные",
        },
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
        403: {"model": schemas.OkResponse, "description": "Отказанно в доступе"},
        404: {"model": schemas.OkResponse, "description": "Категория не найдена"},
    },
    tags=["Административная панель / Подфакты Знакомства"],
)
def delete_sub_interest(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    sub_facts_id: int = Path(..., description="Идентификатор подфакт"),
):
    sub_interest = crud.sub_facts.get_by_id(db, sub_facts_id)
    if sub_interest is None:
        raise UnfoundEntity(message="Подфакт не найден")

    crud.sub_facts.remove(db=db, id=sub_facts_id)

    return schemas.OkResponse()
