from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....exceptions import UnfoundEntity
from ....models import get_full_name
from ....notification.notificator import Notificator
from ....schemas import CreatingOffer, UpdatingOffer, IsWinnerBody

router = APIRouter()


@router.get(
    '/cp/offers/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingOffer],
    name="Получить отклики",
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
    tags=["Административная панель / Отклики"]
)
@router.get(
    '/offers/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingOffer],
    name="Получить отклики",
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
    tags=["Мобильное приложение / Отклики"]
)
def get_offers(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        order_creator_id: Optional[int] = Query(None),
        offer_creator_id: Optional[int] = Query(None),
        order_id: Optional[int] = Query(None),
):

    if order_creator_id is None:
        order_creator = None
    else:
        order_creator = crud.user.get_by_id(db=db,id=order_creator_id)
        if order_creator is None:
            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )
    if offer_creator_id is None:
        offer_creator = None
    else:
        offer_creator = crud.user.get_by_id(db=db,id=offer_creator_id)
        if offer_creator is None:
            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )
    if order_id is None:
        order = None
    else:
        order = crud.order.get_by_id(db=db, id=order_id)
        if order is None:
            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )

    data, paginator = crud.offer.search(db, offer_creator=offer_creator, order_creator=order_creator, order=order,
                                        page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.order.get_offer(db=db, offer=datum,current_user=current_user)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/orders/{order_id}/offers/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOffer],
    name="Создать отклик",
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
    tags=["Мобильное приложение / Отклики"]
)
def create_offer(
        data: CreatingOffer,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        order_id: int = Path(...),
        # notificator: Notificator = Depends(deps.get_notificator),
):
    order = crud.order.get_by_id(db=db, id=order_id)
    if order is None:
        raise UnfoundEntity(num=2, message='Заказ не найден', description='Заказ не найден')
    offer = crud.offer.create_for_user(db=db, obj_in=data, order=order, user=current_user)

    # if order is not None and order.user is not None:
    #     notificator.notify(
    #         title='Пользователь откликнулся на ваш заказ',
    #         recipient=order.user,
    #         text=f'Пользователь {get_full_name(offer.user)} откликнулся на ваш заказ',
    #         icon=offer.user.avatar,
    #         db=db,
    #         order_id=order.id,
    #         offer_id=offer.id,
    #         stage=order.stage.value if order.stage is not None else None
    #     )

    return schemas.SingleEntityResponse(data=getters.order.get_offer(db=db,offer=offer,current_user=current_user))


@router.put(
    '/orders/offers/{offer_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOffer],
    name="Изменить отклик",
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
    tags=["Мобильное приложение / Отклики"]
)
def update_offer(
        data: UpdatingOffer,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        offer_id: int = Path(...)
):
    offer = crud.offer.get_by_id(db=db, id=offer_id)
    if offer is None:
        raise UnfoundEntity(num=2, message='Отклик не найден', description='Отклик не найден')
    offer = crud.offer.update(db=db, obj_in=data, db_obj=offer)
    return schemas.SingleEntityResponse(data=getters.order.get_offer(db=db,offer=offer,current_user=current_user))


@router.put(
    '/orders/offers/{offer_id}/is_winner/',
    response_model=schemas.SingleEntityResponse[schemas.GettingOffer],
    name="Выбрать победителем",
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
    tags=["Мобильное приложение / Отклики"]
)
def update_offer(
        data: IsWinnerBody,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        offer_id: int = Path(...),
        notificator: Notificator = Depends(deps.get_notificator),
):
    offer = crud.offer.get_by_id(db=db, id=offer_id)
    if offer is None:
        raise UnfoundEntity(num=2, message='Отклик не найден', description='Отклик не найден')
    offer = crud.offer.choose_winning_offer(db=db, offer=offer,is_winner=data.is_winner)

    order = offer.order
    if order is not None and order.user is not None:
        notificator.notify(
            title='Пользователь принял ваше предложение',
            recipient=offer.user,
            text=f'Пользователь {get_full_name(order.user)} принял ваше предложение',
            icon=order.user.avatar,
            db=db,
            order_id=order.id,
            offer_id=offer.id,
            stage=order.stage.value if order.stage is not None else None
        )

    return schemas.SingleEntityResponse(data=getters.order.get_offer(db=db,offer=offer,current_user=current_user))


@router.delete(
    '/cp/orders/offers/{offer_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отклик",
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
    tags=["Административная панель / Отклики"]
)
@router.delete(
    '/orders/offers/{offer_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отклик",
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
    tags=["Мобильное приложение / Отклики"]
)
def delete_offer(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        offer_id: int = Path(...)
):
    offer = crud.offer.get_by_id(db=db, id=offer_id)
    if offer is None:
        raise UnfoundEntity(num=2, message='Отклик не найден', description='Отклик не найден')
    crud.offer.remove(db=db, id=offer_id)
    return schemas.OkResponse()
