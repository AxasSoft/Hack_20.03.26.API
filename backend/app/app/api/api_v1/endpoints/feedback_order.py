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
    '/cp/feedbacks/{order_id}',
    response_model=schemas.ListOfEntityResponse[schemas.GettingFeedbackOrder],
    name="Получить отзывы на объявления пользователя",
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
    tags=["Административная панель / Отзывы объявления"]
)
@router.get(
    '/feedbacks/{order_id}',
    response_model=schemas.ListOfEntityResponse[schemas.GettingFeedbackOrder],
    name="Получить отзывы на объявления пользователя",
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
    tags=["Мобильное приложение / Отзывы объявления"]
)
def get_feedbacks(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        order_id: Optional[int] = Query(None),
):
    order = crud.order.get_by_id(db=db, id=order_id)
    if order is None:
        raise UnfoundEntity(num=2, message='объявление не найдено', description='объявление не найдено')
    
    data, paginator = crud.crud_feedback_order.feedback_order.search(
        db,
        order=order,
        user=current_user,
        page=page
    )

    return schemas.ListOfEntityResponse(
        data=[
            getters.feedback_order.get_feedback_order(db=db, feedback=datum)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/order/{order_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedbackOrder],
    name="Создать отзыв на объявления",
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
    tags=["Мобильное приложение / Отзывы объявления"]
)
@router.post(
    '/cp/order/{order_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedbackOrder],
    name="Создать отзыв на объявления",
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
    tags=["Административная панель / Отзывы объявления"]
)
def create_order(
        data: schemas.CreatingFeedbackOrder,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        order_id: int = Path(...),
        notificator: Notificator = Depends(deps.get_notificator),
):
    order = crud.order.get_by_id(db=db, id=order_id)
    if order is None:
        raise UnfoundEntity(num=2, message='объявление не найдено', description='объявление не найдено')
    feedback = crud.crud_feedback_order.feedback_order.create_feedback_for_user(db=db, obj_in=data, order=order, creator=current_user)

    second_user = None
    if order.user == current_user:
        second_user = order.order.user
    elif order.order.user == current_user:
        second_user = order.user

    if second_user is not None:

        notificator.notify(
            title=f'Пользователь {get_full_name(current_user)} оставил отзыв о вас',
            recipient=second_user,
            text=feedback.text,
            icon=current_user.avatar,
            db=db,
            order_id=order.id,
            stage=order.stage.value if order.stage is not None else None
        )

    return schemas.SingleEntityResponse(data=getters.feedback_order.get_feedback_order(db=db,feedback=feedback))



@router.put(
    '/order/{feedback_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedbackOrder],
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
    tags=["Мобильное приложение / Отзывы объявления"]
)
@router.put(
    '/cp/order/{feedback_id}/feedbacks/',
    response_model=schemas.SingleEntityResponse[schemas.GettingFeedbackOrder],
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
    tags=["Административная панель / Отзывы объявления"]
)
def update_feedback(
        data: schemas.feedback_order.UpdatingFeedbackOrder ,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        feedback_id: int = Path(...)
):
    feedback = crud.crud_feedback_order.feedback_order.get_by_id(db=db, id=feedback_id)
    if feedback is None:
        raise UnfoundEntity(num=2, message='Отзыв не найден', description='Отзыв не найден')
    
    if feedback.creator_id != current_user.id:
        raise UnfoundEntity(num=2, message='Вы не можете обновить этот отзыв', description='Вы не можете обновить этот отзыв')

    feedback = crud.crud_feedback_order.feedback_order.update(db=db, obj_in=data, db_obj=feedback)

    return schemas.SingleEntityResponse(data=getters.feedback_order.get_feedback_order(db=db,feedback=feedback))


@router.delete(
    '/cp/order/{feedback_id}/feedbacks/',
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
    tags=["Административная панель / Отзывы объявления"]
)
@router.delete(
    '/order/{feedback_id}/feedbacks/',
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
    tags=["Мобильное приложение / Отзывы объявления"]
)
def delete_offer(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        feedback_id: int = Path(...)
):
    feedback = crud.crud_feedback_order.feedback_order.get_by_id(db=db, id=feedback_id)
    if feedback is None:
        raise UnfoundEntity(num=2, message='Отзыв не найден', description='Отзыв не найден')
    crud.crud_feedback_order.feedback_order.remove(db=db, feedback=feedback)
    return schemas.OkResponse()
