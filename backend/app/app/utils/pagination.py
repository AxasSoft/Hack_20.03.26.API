from typing import Optional, Tuple, List

from paginate_sqlalchemy import SqlalchemyOrmPage

from app.schemas.response import Paginator


def get_page(query, page: Optional[int]) -> Tuple[List, Optional[Paginator]]:
    if page is None:
        return query.all(), None

    page_obj = SqlalchemyOrmPage(query, page=page, items_per_page=30)

    total = page_obj.page_count

    paginator = Paginator(
        page=page,
        total=total,
        has_prev=page > 1,
        has_next=page < total
    )
    return page_obj.items, paginator


def get_page_no_db(elements: List, page: Optional[int]) -> Tuple[List, Optional[Paginator]]:
    if page is None:
        return elements, None

    items_per_page=30
    total = (len(elements) + (items_per_page - 1)) // items_per_page
    if 0 < page <= total:
        list_elements = elements[items_per_page*page:items_per_page*(page+1)]
    else:
        list_elements = []


    paginator = Paginator(
        page=page,
        total=total,
        has_prev=page > 1,
        has_next=page < total
    )
    return list_elements, paginator