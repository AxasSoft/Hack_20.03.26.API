from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/subgenremusic/',
    tags=['Административная панель / Поджанры музыки Знакомства'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubGenreMusic],
    name="Получить все доступные поджанры музыки",
)
@router.get(
    '/subgenremusic/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubGenreMusic],
    name="Получить все доступные поджанры музыки",
    tags=['Мобильное приложение / Поджанры музыки Знакомства'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user)
):
    
    sub_genre_music, total = crud.sub_genre_music.get_sub_genre_music(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.sub_genre_music.get_sub_genre_music(sub_genre_music)
            for sub_genre_music
            in sub_genre_music
        ]
    )

@router.get(
    '/subgenremusic/user',
    response_model=schemas.ListOfEntityResponse[schemas.GettingSubGenreMusic],
    name="Получить все доступные поджанры текущего пользователя",
    tags=['Мобильное приложение / Поджанры музыки Знакомства'],
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
):
    if current_user.is_dating_profile == False:
        raise UnfoundEntity(
            message="У пользователя нет профиля для знакомств"
        )
    sub_genre_music = crud.sub_genre_music.get_sub_genre_music_current_user(db=db, user=current_user)
    return schemas.ListOfEntityResponse(
        data=[
            getters.sub_genre_music.get_sub_genre_music(sub_genre_music)
            for sub_genre_music 
            in sub_genre_music
        ]
    )



@router.post(
    '/cp/subgenremusic/',
    response_model=schemas.SingleEntityResponse[schemas.GettingSubGenreMusic],
    name="Добавить поджанр музыки",
    description="Добавить новый поджанр музыки",
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
    tags=["Административная панель / Поджанры музыки Знакомства"]
)
def create_sub_genre_music(
        data: schemas.CreatingSubGenreMusic,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    genre_music = crud.genre_music.get_by_id(db, data.parent_genre_music_id)
    if genre_music is None:
        raise UnfoundEntity(
            message="Жанр не найден"
        )

    sub_genre_music = crud.sub_genre_music.create_sub_genre_music(db, obj_in=data)
    
    return schemas.SingleEntityResponse(
        data=getters.sub_genre_music.get_sub_genre_music(sub_genre_music)
    )



@router.put(
    '/cp/subgenremusic/{sub_genremusic_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingSubGenreMusic],
    name="Изменить поджанр музыки",
    description="Изменить поджанр музыки",
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
    tags=["Административная панель / Поджанры музыки Знакомства"]
)
def edit_sub_genremusic(
        data: schemas.UpdatingSubGenreMusic,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        sub_genremusic_id: int = Path(..., description="Идентификатор поджанра музыки")
):

    sub_genre_music = crud.sub_genre_music.get_by_id(db, sub_genremusic_id)
    if sub_genre_music is None:
        raise UnfoundEntity(
            message="Поджанр музыки не найден"
        )
    new_sub_genre_music = crud.sub_genre_music.update(db, db_obj=sub_genre_music, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.sub_genre_music.get_sub_genre_music(new_sub_genre_music)
    )


@router.delete(
    '/cp/subgenremusic/{sub_genremusic_id}/',
    response_model=schemas.OkResponse,
    name="Удалить поджанр музыки",
    description="Удалить поджанр музыки",
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
    tags=["Административная панель / Поджанры музыки Знакомства"]
)
def delete_sub_genremusic(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        sub_genremusic_id: int = Path(..., description="Идентификатор поджанра музыки")
):

    sub_genre_music = crud.sub_genre_music.get_by_id(db, sub_genremusic_id)
    if sub_genre_music is None:
        raise UnfoundEntity(
            message="Поджанр музыки не найден"
        )

    crud.sub_genre_music.remove(db=db, id=sub_genremusic_id)

    return schemas.OkResponse()

