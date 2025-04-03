from app.crud.base import CRUDBase
from app.models import Book
from app.schemas import CreatingBook, UpdatingBook


class CRUDBook(CRUDBase[Book, CreatingBook, UpdatingBook]):
    pass


book = CRUDBook(Book)