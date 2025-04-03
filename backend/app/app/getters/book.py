from app.models import Book
from app.schemas import GettingBook


def get_book(book: Book) -> GettingBook:
    return GettingBook(
        id=book.id,
        name=book.name
    )