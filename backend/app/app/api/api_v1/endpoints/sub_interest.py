from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()



@router.get(
    '/subinterests/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubInterest],
    name="Получить все доступные подинтересы",
    tags=['Мобильное приложение / Подинтерес Знакомства'],
)
def get_all(
        db: Session = Depends(deps.get_db)
):
    
    sub_interests, total = crud.sub_interest.get_sub_interests(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.sub_interest.get_sub_interest(sub_interest)
            for sub_interest 
            in sub_interests
        ]
    )


@router.get(
    '/subinterests/user',
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubInterest],
    name="Получить все доступные подинтересы текущего пользователя",
    tags=['Мобильное приложение / Подинтерес Знакомства'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
):
    if current_user.is_dating_profile is None or current_user.is_dating_profile == False:
        raise UnfoundEntity(
            message="У пользователя нет профиля для знакомств"
        )
    sub_interests = crud.sub_interest.get_sub_interests_current_user(db=db, user=current_user)
    return schemas.ListOfEntityResponse(
        data=[
            getters.sub_interest.get_sub_interest(sub_interest)
            for sub_interest 
            in sub_interests
        ]
    )


@router.get(
    '/cp/subinterests/',
    tags=['Административная панель / Подинтерес Знакомства'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubInterest],
    name="Получить все доступные подинтерес",
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    
    sub_interests, total = crud.sub_interest.get_sub_interests(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.sub_interest.get_sub_interest(sub_interest)
            for sub_interest 
            in sub_interests
        ]
    )




@router.post(
    '/cp/subinterests/',
    response_model=schemas.SingleEntityResponse[schemas.GettingSubInterest],
    name="Добавить подинтерес",
    description="Добавить новый подинтерес",
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
    tags=["Административная панель / Подинтерес Знакомства"]
)
def create_sub_interest(
        data: schemas.CreatingSubInterest,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    try:
        sub_interest = crud.sub_interest.create_sub_interest(db, obj_in=data)
    except:
        raise UnfoundEntity(message="Интерес не найден",description="Интерес не найден",num=1)
    

    
    return schemas.SingleEntityResponse(
        data=getters.sub_interest.get_sub_interest(sub_interest)
    )



@router.put(
    '/cp/subinterests/{sub_interest_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingSubInterest],
    name="Изменить подинтерес",
    description="Изменить подинтерес",
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
    tags=["Административная панель / Подинтерес Знакомства"]
)
def edit_interest(
        data: schemas.UpdatingInterest,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        sub_interest_id: int = Path(..., description="Идентификатор подинтерес")
):

    sub_interest = crud.sub_interest.get_by_id(db, sub_interest_id)
    if sub_interest is None:
        raise UnfoundEntity(
            message="Под интерес не найден"
        )
    sub_interest = crud.sub_interest.update(db, db_obj=sub_interest, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.sub_interest.get_sub_interest(sub_interest)
    )


@router.delete(
    '/cp/subinterests/{sub_interest_id}/',
    response_model=schemas.OkResponse,
    name="Удалить под интерес",
    description="Удалить подинтерес",
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
    tags=["Административная панель / Подинтерес Знакомства"]
)
def delete_sub_interest(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        sub_interest_id: int = Path(..., description="Идентификатор под интерес")
):

    sub_interest = crud.sub_interest.get_by_id(db, sub_interest_id)
    if sub_interest is None:
        raise UnfoundEntity(
            message="Интерес не найден"
        )

    crud.sub_interest.remove(db=db, id=sub_interest_id)

    return schemas.OkResponse()

