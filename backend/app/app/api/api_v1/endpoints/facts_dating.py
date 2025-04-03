from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()

@router.get(
    '/facts/all',
    response_model=schemas.ListOfEntityResponse[schemas.FactsSubFacts],
    name="Получить все доступные факты и подфакты",
    tags=['Мобильное приложение / Факты Знакомства'],
)
def get_facts_all(
        # current_user: models.User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db)
):
    all_facts = crud.facts.get_all_facts_subfacts(db)
    
    return schemas.ListOfEntityResponse(
        data=all_facts
    )

@router.get(
    '/facts/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingFacts],
    name="Получить все доступные факты",
    tags=['Мобильное приложение / Факты Знакомства'],
)
@router.get(
    '/cp/facts/',
    tags=['Административная панель / Факты Знакомства'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingFacts],
    name="Получить все доступные факты",
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user)
):
    facts, total = crud.facts.get_facts(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.facts_dating.get_facts(fact)
            for fact
            in facts
        ]
    )


@router.post(
    '/cp/facts/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFacts],
    name="Добавить факт",
    description="Добавить новый факт",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказанно в доступе'
        }
    },
    tags=["Административная панель / Факты Знакомства"]
)
def create_facts(
        data: schemas.CreatingFacts,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    facts = crud.facts.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.facts_dating.get_facts(facts)
    )


@router.put(
    '/cp/facts/{facts_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFacts],
    name="Изменить факт",
    description="Изменить факт",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказано в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Категория не найдена'
        }
    },
    tags=["Административная панель / Факты Знакомства"]
)
def edit_facts(
        data: schemas.UpdatingFacts,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        facts_id: int = Path(..., description="Идентификатор факта")
):

    facts = crud.facts.get_by_id(db, facts_id)
    if facts is None:
        raise UnfoundEntity(
            message="Интерес не найден"
        )
    new_interest = crud.facts.update(db, db_obj=facts, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.facts_dating.get_facts(new_interest)
    )


@router.delete(
    '/cp/facts/{facts_id}/',
    response_model=schemas.OkResponse,
    name="Удалить факт",
    description="Удалить факт",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': schemas.OkResponse,
            'description': 'Категория не найдена'
        }
    },
    tags=["Административная панель / Факты Знакомства"]
)
def delete_facts(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        facts_id: int = Path(..., description="Идентификатор факта")
):

    facts = crud.facts.get_by_id(db, facts_id)
    if facts is None:
        raise UnfoundEntity(
            message="факт не найден"
        )

    crud.facts.remove(db=db, id=facts_id)

    return schemas.OkResponse()



