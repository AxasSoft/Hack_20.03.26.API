from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()



@router.get(
    '/interests/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingInterest],
    name="Получить все доступные интересы",
    tags=['Мобильное приложение / Интересы Знакомств'],
)
def get_all(
        db: Session = Depends(deps.get_db)
):
    interests, total = crud.interests.get_interests(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.interests_dating.get_interest(interest)
            for interest
            in interests
        ]
    )


@router.get(
    '/cp/interests/',
    tags=['Административная панель / Интересы Знакомств'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingInterest],
    name="Получить все доступные интересы",

)
def get_all(
        db: Session = Depends(deps.get_db)
):
    interests, total = crud.interests.get_interests(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.interests_dating.get_interest(interest)
            for interest
            in interests
        ]
    )


@router.post(
    '/cp/interests/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInterest],
    name="Добавить интерес",
    description="Добавить новый интерес",
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
    tags=["Административная панель / Интересы Знакомств"]
)
def create_interest(
        data: schemas.CreatingInterest,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    interests = crud.interests.create(db, obj_in=data)
    return schemas.SingleEntityResponse(
        data=getters.interests_dating.get_interest(interests)
    )


@router.put(
    '/cp/interests/{interest_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingInterest],
    name="Изменить интерес",
    description="Изменить интерес",
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
    tags=["Административная панель / Интересы Знакомств"]
)
def edit_interest(
        data: schemas.UpdatingInterest,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        interest_id: int = Path(..., description="Идентификатор интерес")
):

    interest = crud.interests.get_by_id(db, interest_id)
    if interest is None:
        raise UnfoundEntity(
            message="Интерес не найден"
        )
    interest = crud.interests.update(db, db_obj=interest, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.interests_dating.get_interest(interest)
    )


@router.delete(
    '/cp/interests/{interest_id}/',
    response_model=schemas.OkResponse,
    name="Удалить интерес",
    description="Удалить интерес",
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
    tags=["Административная панель / Интересы Знакомств"]
)
def delete_interest(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        interest_id: int = Path(..., description="Идентификатор интереса")
):

    interest = crud.interests.get_by_id(db, interest_id)
    if interest is None:
        raise UnfoundEntity(
            message="Интерес не найден"
        )

    crud.interests.remove(db=db, id=interest_id)

    return schemas.OkResponse()


@router.get(
    '/interests/all',
    response_model=schemas.ListOfEntityResponse[schemas.InterestsSubinterests],
    name="Получить все доступные подинтересы и интересы",
    tags=['Мобильное приложение / Интересы Знакомств'],
)
def get_all(
        # current_user: models.User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db)
):
    all_interests = crud.interests.get_all_interests_subinterests(db)
    
    return schemas.ListOfEntityResponse(
        data=all_interests
    )


