from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()

@router.get(
    '/genremusic/all',
    response_model=schemas.ListOfEntityResponse[schemas.GenreMusicSubGenreMusic],
    name="Получить все доступные жанры и поджанры музыки",
    tags=['Мобильное приложение / Жанры музыки Знакомства'],
)
def get_all(
        # current_user: models.User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db)
):
    all_interests = crud.genre_music.get_all_genremusic_subgenremusic(db)
    
    return schemas.ListOfEntityResponse(
        data=all_interests
    )




@router.get(
    '/genremusic/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingGenreMusic],
    name="Получить все доступные жанры музыки",
    tags=['Мобильное приложение / Жанры музыки Знакомства'],
)
@router.get(
    '/cp/genremusic/',
    tags=['Административная панель / Жанры музыки Знакомства'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingGenreMusic],
    name="Получить все доступные жанры музыки",
)
def get_all(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user)
):
    genre_music, total = crud.genre_music.get_genremusic(db=db)
    return schemas.ListOfEntityResponse(
        data=[
            getters.genre_music_dating.get_genre_music(genre_music)
            for genre_music
            in genre_music
        ]
    )


@router.post(
    '/cp/genremusic/',
    response_model=schemas.SingleEntityResponse[schemas.GettingGenreMusic],
    name="Добавить жанр музыки",
    description="Добавить новый жанр музыки",
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
    tags=["Административная панель / Жанры музыки Знакомства"]
)
def create_interest(
        data: schemas.CreatingGenreMusic,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    genre_music = crud.genre_music.create(db, obj_in=data)
    return schemas.SingleEntityResponse(
        data=getters.genre_music_dating.get_genre_music(genre_music)
    )


@router.put(
    '/cp/genremusic/{genremusic_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingGenreMusic],
    name="Изменить жанр музыки",
    description="Изменить жанр музыки",
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
    tags=["Административная панель / Жанры музыки Знакомства"]
)
def edit_genre_music(
        data: schemas.CreatingGenreMusic,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        genremusic_id: int = Path(..., description="Идентификатор жанра музыки")
):

    genre_music = crud.genre_music.get_by_id(db, genremusic_id)
    if genre_music is None:
        raise UnfoundEntity(
            message="Жанр не найден"
        )
    new_genre_music = crud.genre_music.update(db, db_obj=genre_music, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.genre_music_dating.get_genre_music(new_genre_music)
    )


@router.delete(
    '/cp/genremusic/{genremusic_id}/',
    response_model=schemas.OkResponse,
    name="Удалить жанр музыки",
    description="Удалить жанр музыки",
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
    tags=["Административная панель / Жанры музыки Знакомства"]
)
def delete_genre_music(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        genremusic_id: int = Path(..., description="Идентификатор поджанра музыки")
):

    genre_music = crud.genre_music.get_by_id(db, genremusic_id)
    if genre_music is None:
        raise UnfoundEntity(
            message="Поджанр музыки не найден"
        )

    crud.genre_music.remove(db=db, id=genremusic_id)

    return schemas.OkResponse()


