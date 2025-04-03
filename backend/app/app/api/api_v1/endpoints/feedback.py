import logging
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
from ....schemas import CreatingFeedback, UpdatingFeedback

router = APIRouter()


@router.get(
    '/cp/feedbacks/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingFeedback],
    name="Получить отзывы",
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
    tags=["Административная панель / Отзывы"]
)
@router.get(
    '/feedbacks/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingFeedback],
    name="Получить отзывы",
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
    tags=["Мобильное приложение / Отзывы"]
)
def get_feedbacks(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        offer_id: Optional[int] = Query(None),
        order_id: Optional[int] = Query(None),
        by_user_id: Optional[int] = Query(None),
        about_user_id: Optional[int] = Query(None)
):

    if order_id is None:
        order = None
    else:
        order = crud.order.get_by_id(db=db, id=order_id)
        if order is None:
            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )
    if offer_id is None:
        offer = None
    else:
        offer = crud.offer.get_by_id(db=db, id=offer_id)
        if offer is None:
            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )
    if by_user_id is None:
        by_user = None
    else:
        by_user = crud.user.get_by_id(db=db,id=by_user_id)
        if by_user is None:

            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )
    if about_user_id is None:
        about_user = None
    else:
        about_user = crud.user.get_by_id(db=db, id=about_user_id)
        if about_user is None:
            return schemas.ListOfEntityResponse(
                data=[],
                meta=Meta()
            )

    data, paginator = crud.feedback.search(
        db,
        offer=offer,
        order=order,
        about_user=about_user,
        by_user=by_user,
        page=page
    )

    return schemas.ListOfEntityResponse(
        data=[
            getters.feedback.get_feedback(datum)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/offers/{offer_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedback],
    name="Создать отзыв",
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
    tags=["Мобильное приложение / Отзывы"]
)
@router.post(
    '/cp/offers/{offer_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedback],
    name="Создать отзыв",
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
    tags=["Административная панель / Отзывы"]
)
def create_offer(
        data: CreatingFeedback,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        offer_id: int = Path(...),
        notificator: Notificator = Depends(deps.get_notificator),
):
    offer = crud.offer.get_by_id(db=db, id=offer_id)
    if offer is None:
        raise UnfoundEntity(num=2, message='Отклик не найден', description='Отклик не найден')
    feedback = crud.feedback.create_for_user(db=db, obj_in=data, offer=offer, user=current_user)

    second_user = None
    if offer.user == current_user:
        second_user = offer.order.user
    elif offer.order.user == current_user:
        second_user = offer.user

    if second_user is not None:

        notificator.notify(
            title=f'Пользователь {get_full_name(current_user)} оставил отзыв о вас',
            recipient=second_user,
            text=feedback.text,
            icon=current_user.avatar,
            db=db,
            order_id=offer.order.id,
            offer_id=offer.id,
            stage=offer.order.stage.value if offer.order.stage is not None else None
        )

    return schemas.SingleEntityResponse(data=getters.feedback.get_feedback(feedback))


@router.post(
    '/cp/users/{user_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedback],
    name="Создать отзыв на пользователя",
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
    tags=["Административная панель / Отзывы"]
)
def create_offer(
        data: CreatingFeedback,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        user_id: int = Path(...)
):
    user = crud.user.get_by_id(db=db, id=user_id)
    if user is None:
        raise UnfoundEntity(num=2, message='Пользователь не найден', description='Пользователь не найден')
    feedback = crud.feedback.create_for_user(db=db, obj_in=data, offer=None, user=current_user, second_user=user)
    return schemas.SingleEntityResponse(data=getters.feedback.get_feedback(feedback))


@router.put(
    '/offers/feedbacks/{feedback_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedback],
    name="Изменить отзыв",
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
    tags=["Мобильное приложение / Отзывы"]
)
@router.put(
    '/cp/offers/feedbacks/{feedback_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedback],
    name="Изменить отзыв",
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
    tags=["Административная панель / Отзывы"]
)
def update_feedback(
        data: UpdatingFeedback,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        feedback_id: int = Path(...)
):
    feedback = crud.feedback.get_by_id(db=db, id=feedback_id)
    if feedback is None:
        raise UnfoundEntity(num=2, message='Отзыв не найден', description='Отзыв не найден')
    feedback = crud.feedback.update(db=db, obj_in=data, db_obj=feedback)
    return schemas.SingleEntityResponse(data=getters.feedback.get_feedback(feedback))


@router.delete(
    '/cp/offers/feedbacks/{feedback_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отзыв",
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
    tags=["Административная панель / Отзывы"]
)
@router.delete(
    '/offers/feedbacks/{feedback_id}/',
    response_model=schemas.OkResponse,
    name="Удалить отзыв",
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
    tags=["Мобильное приложение / Отзывы"]
)
def delete_offer(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        feedback_id: int = Path(...)
):
    feedback = crud.feedback.get_by_id(db=db, id=feedback_id)
    if feedback is None:
        raise UnfoundEntity(num=2, message='Отзыв не найден', description='Отзыв не найден')
    crud.feedback.remove(db=db, id=feedback_id)
    return schemas.OkResponse()
