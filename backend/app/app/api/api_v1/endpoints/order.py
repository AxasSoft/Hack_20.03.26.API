from io import BytesIO
import datetime
from io import BytesIO
from typing import List, Optional

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from fastapi.params import File, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....enums.mod_status import ModStatus
from ....exceptions import UnfoundEntity, InaccessibleEntity
from ....models import Offer, get_full_name
from ....models.order import Stage
from ....notification.notificator import Notificator
from ....schemas import CreatingOrder, UpdatingOrder, BlockBody
import logging


from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/ads/export/',
    name="Экспортировать данные объявлений",
    tags=['Административная панель / Объявления'],
)

def export(
        db: Session = Depends(deps.get_db),
):
    data = crud.order.export(db)
    export_media_type = 'text/csv'

    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')

    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}-{dt}.csv".format(file_name='ads',dt=now)
    }
    return StreamingResponse(BytesIO(data), headers=export_headers, media_type=export_media_type)


def adapt_statuses(statuses):
    if statuses is None:
        return None
    else:
        return [ModStatus(status) for status in statuses]


@router.get(
    '/users/me/ads/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingOrderWithWinner],
    name="Получить все объявления текущего пользователя",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def get_order_with_winners_by_user(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        address: Optional[str] = Query(None),
        type: Optional[str] = Query(None),
        is_winner: Optional[bool] = Query(None),
        current_user: models.User = Depends(deps.get_current_active_user),
        category_id: Optional[int] = Query(None),
        subcategory_id: Optional[int] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        statuses: Optional[List[int]] = Query(None),
        cache: Cache = Depends(deps.get_cache_list),
):

    def fatch_order():
        if is_winner:
            stages = [Stage.created, Stage.selected]
        else:
            stages = [Stage.created,Stage.finished,Stage.selected]


        data, paginator = crud.order.search(
            db,
            user=current_user,
            page=page,
            address=address,
            type=type,
            stages=stages,
            current_user=current_user,
            is_winner=is_winner,
            category_id=category_id,
            subcategory_id=subcategory_id,
            is_favorite=is_favorite,
            statuses=adapt_statuses(statuses)
        )

        [crud.crud_order.order.make_view(db=db, order_id=order.id, user_id=current_user.id) for order in data]

        return schemas.ListOfEntityResponse(
            data=[
                getters.order.get_order_with_winner(db, datum, current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )


    key_tuple = ('order_by_user', f"user - {current_user.id} - page - {page} - address - {address} - type - {type} - \
                 is_winner - {is_winner} - category_id - {category_id} - subcategory_id - {subcategory_id} - is_favorite -{is_favorite} -\
                    statuses - {statuses}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_order, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data

@router.get(
    '/users/{user_id}/ads/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingOrderWithWinner],
    name="Получить все объявления пользователя",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def get_order_with_winners_by_user(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        user_id: int = Path(...),
        current_user: models.User = Depends(deps.get_current_active_user),
        address: Optional[str] = Query(None),
        type: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        subcategory_id: Optional[int] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        statuses: Optional[List[int]] = Query(None),
        cache: Cache = Depends(deps.get_cache_list),
):
    def fatch_order_user():
        user = crud.user.get_by_id(db,id=user_id)
        if user is None:
            raise UnfoundEntity(message='Пользователь не найден', num=2)

        data, paginator = crud.order.search(
            db,
            user=user,
            page=page,
            stages=[Stage.created],
            is_block=False,
            address=address,
            type=type,
            category_id=category_id,
            subcategory_id=subcategory_id,
            is_favorite=is_favorite,
            statuses=adapt_statuses(statuses)
        )

        return schemas.ListOfEntityResponse(
            data=[
                getters.order.get_order_with_winner(db, datum, current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )
    

    key_tuple = ('order_by_user', f"user_id - {user_id} - page - {page} - address - {address} - type - {type} - \
                 category_id - {category_id} - subcategory_id - {subcategory_id} - is_favorite -{is_favorite} -\
                    statuses - {statuses}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_order_user, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.get(
    '/cp/ads/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingOrderWithWinner],
    name="Получить все объявления",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Административная панель / Объявления"]
)
def get_order_with_winners(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        user_id: Optional[int] = Query(None),
        stages: Optional[List[int]] = Query(None),
        is_block: Optional[bool] = Query(None),
        address: Optional[str] = Query(None),
        type: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        subcategory_id: Optional[int] = Query(None),
        statuses: Optional[List[int]] = Query(None),
        min_price: Optional[int] = Query(None),
        max_price: Optional[int] = Query(None), 
        sort_by: Optional[str] = Query(None, title="Сортировка", description="`date_asc` - по дате создания в порядке возрастания., \
                                        `date_desc` по дате создания в порядке убывания. `price_asc` - Сортировка по возрастанию, \
                                        `price_desc` -  в порядке убывания."),
        is_stopping: Optional[bool] = Query(None, title="Активные объявления", description="Отсортировать по активным объявлениям"),

):

    if user_id is not None:
        user = crud.user.get_by_id(db,id=user_id)
        if user is None:
            raise UnfoundEntity(message='Пользователь не найден', num=2)
    else:
        user = None

    if stages is not None:
        stages = [Stage(stage) for stage in stages]

    data, paginator = crud.order.search(
        db,
        page=page,
        stages=stages,
        is_block=is_block,
        user=user,
        address=address,
        type=type,
        category_id=category_id,
        subcategory_id=subcategory_id,
        is_favorite=None,
        statuses=adapt_statuses(statuses),
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        is_stopping=is_stopping
    )

    [crud.crud_order.order.make_view(db=db, order_id=order.id, user_id=current_user.id) for order in data]

    return schemas.ListOfEntityResponse(
        data=[
            getters.order.get_order_with_winner(db, datum, current_user)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.get(
    '/ads/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingOrderWithWinner],
    name="Получить все объявления",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def get_order_with_winners(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        address: Optional[str] = Query(None),
        type: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        subcategory_id: Optional[int] = Query(None),
        is_favorite: Optional[bool] = Query(None),
        statuses: Optional[List[int]] = Query(None),
        min_price: Optional[int] = Query(None),
        max_price: Optional[int] = Query(None), 
        sort_by: Optional[str] = Query(None, title="Сортировка", description="`date_asc` - по дате создания в порядке возрастания., \
                                        `date_desc` по дате создания в порядке убывания. `price_asc` - Сортировка по возрастанию, \
                                        `price_desc` -  в порядке убывания."),
        is_stopping: Optional[bool] = Query(None, title="Активные объявления", description="Отсортировать по активным объявлениям"),
        cache: Cache = Depends(deps.get_cache_list),
):

    def fatch_order_all():
        data, paginator = crud.order.search(
            db,
            page=page,
            stages=[Stage.created],
            current_user=current_user,
            is_block=False,
            address=address,
            type=type,
            category_id=category_id,
            subcategory_id=subcategory_id,
            is_favorite=is_favorite,
            statuses=adapt_statuses(statuses),
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            is_stopping=is_stopping
        )

        [crud.crud_order.order.make_view(db=db, order_id=order.id, user_id=current_user.id) for order in data]

        return schemas.ListOfEntityResponse(
            data=[
                getters.order.get_order_with_winner(db, datum, current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )
    

    key_tuple = ('order_by_user', f"page - {page} - address - {address} - type - {type} - \
                 category_id - {category_id} - subcategory_id - {subcategory_id} - is_favorite -{is_favorite} -\
                    statuses - {statuses} - min_price - {min_price} - max_price - {max_price} - sort_by - {sort_by} -\
                        is_stopping - {is_stopping}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_order_all, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.get(
    '/cp/ads/{ads_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Получить объявления по индетификатору",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Административная панель / Объявления"]
)
def get_order_with_winners(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        ads_id: int = Path(..., description="Идентификатор фильма"),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def fatch_order_id():
        data = crud.order.get_by_id( db, id=ads_id)
        if data is None:
                raise UnfoundEntity(message='Объявление не найдено', num=2)
        
        crud.crud_order.order.make_view(db=db, order_id=ads_id, user_id=current_user.id)

        return schemas.SingleEntityResponse(
            data=getters.order.get_order_with_winner(db, data, current_user)
        )

    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_order_id, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data

@router.get(
    '/ads/{ads_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Получить объявления по индетификатору",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def get_order_with_winners(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        ads_id: int = Path(..., description="Идентификатор объявления"),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def fatch_order_id():
        data = crud.order.get_by_id(db, id=ads_id)
        if data is None:
                raise UnfoundEntity(message='Объявление не найдено', num=2)
        
        crud.crud_order.order.make_view(db=db, order_id=ads_id, user_id=current_user.id)

        return schemas.SingleEntityResponse(
            data=getters.order.get_order_with_winner(db, data, current_user)
        )

    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_order_id, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data



@router.post(
    '/ads/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Добавить новое объявление",
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
            'description': 'ХПользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def add_new_order(
        data: CreatingOrder,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    d = data.dict(exclude_unset=True)
    if 'subcategory_id' in d:
        subcategory = crud.crud_subcategory.subcategory.get_by_id(db=db, id=d['subcategory_id'])
        if subcategory is None:
            raise UnfoundEntity(message='Подкатегория не найдена')
    
    data = crud.order.create_by_user(db, user=current_user, obj_in=data)

    crud.crud_order.order.make_view(db=db, order_id=data.id, user_id=current_user.id)

    return schemas.SingleEntityResponse(
        data=getters.order.get_order_with_winner(db, data, current_user)
    )


@router.put(
    '/ads/{ads_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Изменить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def edit_order(
        data: UpdatingOrder,
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)

    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="Объявление не найдено", description="Объявление не найдено", num=1)

    if order.user != current_user:
        raise InaccessibleEntity(
            message="История не принадлежит пользователю",
            description="История не принадлежит пользователю"
        )

    d = data.dict(exclude_unset=True)
    if 'subcategory_id' in d:
        subcategory = crud.crud_subcategory.subcategory.get_by_id(db=db,id=d['subcategory_id'])
        if subcategory is None:
            raise UnfoundEntity(message='Подкатегория не найдена')

    order = crud.order.update(db, db_obj=order, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.order.get_order_with_winner(db, order, current_user)
    )


@router.put(
    '/ads/{ads_id}/is_rejected/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Отклонить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def reject_order(
        data: BaseModel,
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="Объявление не найден", description="Объявление не найден", num=1)

    if order.user != current_user:
        raise InaccessibleEntity(
            message="История не принадлежит пользователю",
            description="История не принадлежит пользователю"
        )

    order = crud.order.change_stage(db, order=order, stage=Stage.rejected)

    return schemas.SingleEntityResponse(
        data=getters.order.get_order_with_winner(db, order, current_user)
    )


@router.put(
    '/ads/{ads_id}/is_finished/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Завершить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def finish_order(
        data: BaseModel,
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="Объявление не найдено", description="Объявление не найдено", num=1)

    order = crud.order.change_stage(db, order=order, stage=Stage.finished)

    win_offer = db.query(Offer).filter(Offer.order_id == ads_id, Offer.is_winner).first()
    if win_offer is not None and win_offer.user is not None:
        notificator.notify(
            title='Пользователь завершил работу над заказом',
            recipient=order.user,
            text=f'Пользователь {get_full_name(win_offer.user)} завершил работу над заказом {order.title}',
            icon=None,
            db=db,
            order_id=ads_id,
            offer_id=win_offer.id,
            stage=order.stage.value if order.stage is not None else None
        )


    return schemas.SingleEntityResponse(
        data=getters.order.get_order_with_winner(db, order, current_user)
    )


@router.put(
    '/ads/{ads_id}/is_confirmed/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Подтвердить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def confirm_order(
        data: BaseModel,
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="объявление не найдено", description="Объявление не найдено", num=1)

    if order.user != current_user:
        raise InaccessibleEntity(
            message="История не принадлежит пользователю",
            description="История не принадлежит пользователю"
        )

    order = crud.order.change_stage(db, order=order, stage=Stage.confirmed)

    win_offer = db.query(Offer).filter(Offer.order_id == ads_id, Offer.is_winner).first()
    if win_offer is not None and win_offer.user is not None:
        notificator.notify(
            title='Пользователь подтвердил выполнение заказа',
            recipient=win_offer.user,
            text=f'Пользователь {get_full_name(order.user)} подтвердил выполнение заказа {order.title}',
            icon=order.user.avatar,
            db=db,
            order_id=ads_id,
            offer_id=win_offer.id,
            stage=order.stage.value if order.stage is not None else None
        )

    return schemas.SingleEntityResponse(
        data=getters.order.get_order_with_winner(db, order, current_user)
    )


@router.put(
    '/cp/ads/{ads_id}/is_block/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrderWithWinner],
    name="Заблокировать объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Административная панель / Объявления"]
)
def block_order(
        data: BlockBody,
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="Объявление не найдено", description="Объявления не найдено", num=1)

    order = crud.order.change_block(db, order=order, is_block=data.is_block,comment=data.comment)
    if data.is_block:
        notificator.notify(
            title='Ваше объявление заблокировано',
            recipient=order.user,
            text=f'Ваше объявление {order.title} заблокировано администрацией',
            icon=None,
            db=db,
            order_id=ads_id
        )
    else:
        notificator.notify(
            title='Ваше объявление разблокирован',
            recipient=order.user,
            text=f'Ваше объявление {order.title} pазблокировано администрацией',
            icon=None,
            db=db,
            order_id=ads_id
        )

    return schemas.SingleEntityResponse(
        data=getters.order.get_order_with_winner(db, order, current_user)
    )


@router.delete(
    '/cp/ads/{ads_id}/',
    response_model=schemas.OkResponse,
    name="Удалить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Административная панель / Объявления"]
)
@router.delete(
    '/offers/ads/{ads_id}/',
    response_model=schemas.OkResponse,
    name="Удалить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def delete_offer(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        ads_id: int = Path(...),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order = crud.order.get_by_id(db=db, id=ads_id)
    if order is None:
        raise UnfoundEntity(num=2, message='Объявление не найдено', description='Объявление не найдено')
    crud.order.remove(db=db, id=ads_id)
    return schemas.OkResponse()


@router.post(
    '/ads/{ads_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.order.GettingOrder],
    name="Добавить изображение в объявление",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Мобильное приложение / Объявления"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        image: UploadFile = File(...),
        num: Optional[int] = None,
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        ads_id: int = Path(..., title='Идентификатор объявления'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order = crud.crud_order.order.get_by_id(db=db, id=ads_id)
    if order is None:
        raise UnfoundEntity(num=1, message='Объявление не найдено')

    crud.crud_order.order.s3_client = s3_client
    crud.crud_order.order.s3_bucket_name = s3_bucket_name
    crud.crud_order.order.add_image(db=db, order=order, image=image, num=num)
    order.is_accepted = None
    db.add(order)
    db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.order.get_order(db=db, order=order, current_user=current_user)
    )


@router.post(
    '/cp/ads/{ads_id}/images/',
    response_model=schemas.response.SingleEntityResponse[schemas.order.GettingOrder],
    name="Добавить изображение в объявление",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Объявления"]
)
def add_image(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        image: UploadFile = File(...),
        num: Optional[int] = Form(None),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        ads_id: int = Path(..., title='Идентификатор объявления'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order = crud.crud_order.order.get_by_id(db=db, id=ads_id)
    if order is None:
        raise UnfoundEntity(num=1, message='Объявление не найден')

    crud.crud_order.order.s3_client = s3_client
    crud.crud_order.order.s3_bucket_name = s3_bucket_name
    crud.crud_order.order.add_image(db=db, order=order, image=image, num=num)
    order.is_accepted = None
    db.add(order)
    db.commit()
    return schemas.response.SingleEntityResponse(
        data=getters.order.get_order(order=order, current_user=current_user, db=db)
    )


@router.delete(
    '/ads/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.order.GettingOrder],
    name="Удалить изображение объявления",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Мобильное приложение / Объявления"]
)
@router.delete(
    '/cp/ads/images/{image_id}/',
    response_model=schemas.response.SingleEntityResponse[schemas.order.GettingOrder],
    name="Удалить изображение объявления",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Объявления"]
)
def delete_image(
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(
            deps.get_current_user
        ),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        image_id: int = Path(..., title='Идентификатор объявления'),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    key_tuple = ('order_by_id', f"ads_id - {ads_id}")
    cache.delete(key_tuple)
    order_image = crud.crud_order.order.get_image_by_id(db=db, id=image_id)
    if order_image is None:
        raise UnfoundEntity(num=1, message='Картинка не найдена')

    crud.crud_order.order.s3_client = s3_client
    crud.crud_order.order.s3_bucket_name = s3_bucket_name
    crud.crud_order.order.delete_image(db=db, image=order_image)
    return schemas.response.SingleEntityResponse(
        data=getters.order.get_order(order=order_image.order, current_user=current_user, db=db)
    )


@router.put(
    '/ads/{ads_id}/is-favorite/',
    response_model=schemas.response.SingleEntityResponse[
        schemas.order.GettingOrder],
    name="Добавить или убрать в избранное",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Мобильное приложение / Объявления"]
)
def edit_order(
        data: schemas.order.IsFavoriteBody,
        ads_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    order = crud.crud_order.order.get_by_id(db=db, id=ads_id)

    if order is None:
        raise UnfoundEntity(num=1, message='Объявление не найдено')

    crud.crud_order.order.change_is_favorite(
        db=db,
        order=order,
        user=current_user,
        is_favorite=data.is_favorite
    )

    return schemas.response.SingleEntityResponse(
        data=getters.order.get_order(
            order=order, db=db, current_user=current_user)
    )


@router.put(
    '/cp/ads/{ads_id}/moderation/',
    response_model=schemas.response.SingleEntityResponse[
        schemas.order.GettingOrder],
    name="Проверить объявление",
    responses={
        400: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.response.OkResponse,
            'description': 'Переданы некорректные данные'
        },
        403: {
            'model': schemas.response.OkResponse,
            'description': 'Отказано в доступе'
        },
    },
    tags=["Панель управления / Объявления"]
)
def edit_order(
        data: schemas.order.ModerationBody,
        ads_id: int = Path(...),
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_active_superuser),
):

    order = crud.crud_order.order.get_by_id(db=db, id=ads_id)

    if order is None:
        raise UnfoundEntity(num=1, message='Объявление не найдено')

    crud.crud_order.order.moderate(
        db=db,
        order=order,
        moderation_body=data
    )

    return schemas.response.SingleEntityResponse(
        data=getters.order.get_order(
            order=order, db=db, current_user=current_user)
    )



@router.post(
    '/ads/{ads_id}/stopping/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrder],
    name="Приостановить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def stopping_order(
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="Объявление не найдено", description="Объявление не найдено", num=1)
    if order.is_stopping:
        raise UnfoundEntity(message="Объявление уже остановлено", description="Объявление уже остановлено", num=1)
    dict_order = {
        'is_stopping': True
    }
    
    order_is_stop = crud.order.update(db=db, db_obj=order, obj_in=dict_order)

    return schemas.SingleEntityResponse(
        data=getters.order.get_order(db, order_is_stop, current_user)
    )


@router.post(
    '/ads/{ads_id}/reopen/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOrder],
    name="Возобновить объявление",
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
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Объявления"]
)
def reopen_order(
        ads_id: int = Path(..., title="Идентификатор объявления"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('order_by_user')
    order = crud.order.get_by_id(db, id=ads_id)
    if order is None:
        raise UnfoundEntity(message="Объявление не найдено", description="Объявление не найдено", num=1)
    if order.is_stopping is False:
        raise UnfoundEntity(message="Объявление уже активно", description="Объявление уже активно", num=1)
    dict_order = {
        'is_stopping': False
    }
    
    order_is_stop = crud.order.update(db=db, db_obj=order, obj_in=dict_order)

    return schemas.SingleEntityResponse(
        data=getters.order.get_order(db, order_is_stop, current_user)
    )