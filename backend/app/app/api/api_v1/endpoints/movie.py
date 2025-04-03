# from fastapi import APIRouter, Depends
# from fastapi.params import Path
# from sqlalchemy.orm import Session

# from app import crud, models, schemas, getters
# from app.api import deps
# from ....exceptions import UnfoundEntity

# router = APIRouter()



# @router.get(
#     '/movies/',
#     response_model=schemas.ListOfEntityResponse[schemas.GettingMovie],
#     name="Получить все доступные фильмы",
#     tags=['Мобильное приложение / Фильмы'],
# )
# def get_all(
#         db: Session = Depends(deps.get_db)
# ):
#     return schemas.ListOfEntityResponse(
#         data=[
#             getters.movie.get_movie(movie)
#             for movie
#             in crud.movie.get_multi(db=db, page=None)[0]
#         ]
#     )


# @router.get(
#     '/cp/movies/',
#     tags=['Административная панель / Фильмы'],
#     response_model=schemas.ListOfEntityResponse[schemas.GettingMovie],
#     name="Получить все доступные фильмы",

# )
# def get_all(
#         db: Session = Depends(deps.get_db)
# ):
#     return schemas.ListOfEntityResponse(
#         data=[
#             getters.movie.get_movie(movie)
#             for movie
#             in crud.movie.get_multi(db=db, page=None)[0]
#         ]
#     )


# @router.post(
#     '/cp/movies/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingMovie],
#     name="Добавить фильм",
#     description="Добавить новый фильм",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданны невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         },
#         403: {
#             'model': schemas.OkResponse,
#             'description': 'Отказанно в доступе'
#         }
#     },
#     tags=["Административная панель / Фильмы"]
# )
# def create_movie(
#         data: schemas.CreatingMovie,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
# ):

#     movie = crud.movie.create(db, obj_in=data)

#     return schemas.SingleEntityResponse(
#         data=getters.movie.get_movie(movie)
#     )


# @router.put(
#     '/cp/movies/{movie_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingMovie],
#     name="Изменить фильм",
#     description="Изменить фильм",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданы невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         },
#         403: {
#             'model': schemas.OkResponse,
#             'description': 'Отказано в доступе'
#         },
#         404: {
#             'model': schemas.OkResponse,
#             'description': 'Категория не найдена'
#         }
#     },
#     tags=["Административная панель / Фильм"]
# )
# def edit_movie(
#         data: schemas.UpdatingMovie,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         movie_id: int = Path(..., description="Идентификатор фильма")
# ):

#     movie = crud.movie.get_by_id(db, movie_id)
#     if movie is None:
#         raise UnfoundEntity(
#             message="Фильм не найден"
#         )
#     movie = crud.movie.update(db, db_obj=movie, obj_in=data)

#     return schemas.SingleEntityResponse(
#         data=getters.movie.get_movie(movie)
#     )


# @router.delete(
#     '/cp/movies/{movie_id}/',
#     response_model=schemas.OkResponse,
#     name="Удалить фильм",
#     description="Удалить фильм",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданны невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         },
#         403: {
#             'model': schemas.OkResponse,
#             'description': 'Отказанно в доступе'
#         },
#         404: {
#             'model': schemas.OkResponse,
#             'description': 'Категория не найдена'
#         }
#     },
#     tags=["Административная панель / Фильмы"]
# )
# def delete_movie(
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         movie_id: int = Path(..., description="Идентификатор фильма")
# ):

#     movie = crud.movie.get_by_id(db, movie_id)
#     if movie is None:
#         raise UnfoundEntity(
#             message="Фильм не найден"
#         )

#     crud.movie.remove(db=db, id=movie_id)

#     return schemas.OkResponse()
