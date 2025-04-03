# from fastapi import APIRouter, Depends
# from fastapi.params import Path
# from sqlalchemy.orm import Session

# from app import crud, models, schemas, getters
# from app.api import deps
# from ....exceptions import UnfoundEntity

# router = APIRouter()



# @router.get(
#     '/musics/',
#     response_model=schemas.ListOfEntityResponse[schemas.GettingMusic],
#     name="Получить все доступные музыки",
#     tags=['Мобильное приложение / Музыки'],
# )
# def get_all(
#         db: Session = Depends(deps.get_db)
# ):
#     return schemas.ListOfEntityResponse(
#         data=[
#             getters.music.get_music(music)
#             for music
#             in crud.music.get_multi(db=db, page=None)[0]
#         ]
#     )


# @router.get(
#     '/cp/musics/',
#     tags=['Административная панель / Музыки'],
#     response_model=schemas.ListOfEntityResponse[schemas.GettingMusic],
#     name="Получить все доступные музыки",

# )
# def get_all(
#         db: Session = Depends(deps.get_db)
# ):
#     return schemas.ListOfEntityResponse(
#         data=[
#             getters.music.get_music(music)
#             for music
#             in crud.music.get_multi(db=db, page=None)[0]
#         ]
#     )


# @router.post(
#     '/cp/musics/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingMusic],
#     name="Добавить музыку",
#     description="Добавить новую музыку",
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
#     tags=["Административная панель / Музыки"]
# )
# def create_music(
#         data: schemas.CreatingMusic,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
# ):

#     music = crud.music.create(db, obj_in=data)

#     return schemas.SingleEntityResponse(
#         data=getters.music.get_music(music)
#     )


# @router.put(
#     '/cp/musics/{music_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingMusic],
#     name="Изменить музыку",
#     description="Изменить музыку",
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
#     tags=["Административная панель / Музыки"]
# )
# def edit_music(
#         data: schemas.UpdatingMusic,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         music_id: int = Path(..., description="Идентификатор музыку")
# ):

#     music = crud.music.get_by_id(db, music_id)
#     if music is None:
#         raise UnfoundEntity(
#             message="Музыка не найдена"
#         )
#     music = crud.music.update(db, db_obj=music, obj_in=data)

#     return schemas.SingleEntityResponse(
#         data=getters.music.get_music(music)
#     )


# @router.delete(
#     '/cp/musics/{music_id}/',
#     response_model=schemas.OkResponse,
#     name="Удалить музыку",
#     description="Удалить музыку",
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
#     tags=["Административная панель / Музыки"]
# )
# def delete_music(
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         music_id: int = Path(..., description="Идентификатор музыки")
# ):

#     music = crud.music.get_by_id(db, music_id)
#     if music is None:
#         raise UnfoundEntity(
#             message="Музыка не найдена"
#         )

#     crud.music.remove(db=db, id=music_id)

#     return schemas.OkResponse()
