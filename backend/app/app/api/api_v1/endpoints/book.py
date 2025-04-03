# from fastapi import APIRouter, Depends
# from fastapi.params import Path
# from sqlalchemy.orm import Session

# from app import crud, models, schemas, getters
# from app.api import deps
# from ....exceptions import UnfoundEntity

# router = APIRouter()



# @router.get(
#     '/books/',
#     response_model=schemas.ListOfEntityResponse[schemas.GettingBook],
#     name="Получить все доступные книги",
#     tags=['Мобильное приложение / Книги'],
# )
# def get_all(
#         db: Session = Depends(deps.get_db)
# ):
#     return schemas.ListOfEntityResponse(
#         data=[
#             getters.book.get_book(book)
#             for book
#             in crud.book.get_multi(db=db, page=None)[0]
#         ]
#     )


# @router.get(
#     '/cp/books/',
#     tags=['Административная панель / Книги'],
#     response_model=schemas.ListOfEntityResponse[schemas.GettingBook],
#     name="Получить все доступные книги",

# )
# def get_all(
#         db: Session = Depends(deps.get_db)
# ):
#     return schemas.ListOfEntityResponse(
#         data=[
#             getters.book.get_book(book)
#             for book
#             in crud.book.get_multi(db=db, page=None)[0]
#         ]
#     )


# @router.post(
#     '/cp/books/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingBook],
#     name="Добавить книгу",
#     description="Добавить новый книгу",
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
#     tags=["Административная панель / Книги"]
# )
# def create_book(
#         data: schemas.CreatingBook,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
# ):

#     book = crud.book.create(db, obj_in=data)

#     return schemas.SingleEntityResponse(
#         data=getters.book.get_book(book)
#     )


# @router.put(
#     '/cp/books/{book_id}/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingBook],
#     name="Изменить книгу",
#     description="Изменить книгу",
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
#     tags=["Административная панель / Книги"]
# )
# def edit_book(
#         data: schemas.UpdatingBook,
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         book_id: int = Path(..., description="Идентификатор книгу")
# ):

#     book = crud.book.get_by_id(db, book_id)
#     if book is None:
#         raise UnfoundEntity(
#             message="Книга не найдена"
#         )
#     book = crud.book.update(db, db_obj=book, obj_in=data)

#     return schemas.SingleEntityResponse(
#         data=getters.book.get_book(book)
#     )


# @router.delete(
#     '/cp/books/{book_id}/',
#     response_model=schemas.OkResponse,
#     name="Удалить книгу",
#     description="Удалить книгу",
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
#     tags=["Административная панель / Книги"]
# )
# def delete_book(
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         book_id: int = Path(..., description="Идентификатор книги")
# ):

#     book = crud.book.get_by_id(db, book_id)
#     if book is None:
#         raise UnfoundEntity(
#             message="Книга не найдена"
#         )

#     crud.book.remove(db=db, id=book_id)

#     return schemas.OkResponse()
