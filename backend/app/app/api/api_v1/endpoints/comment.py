from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....exceptions import UnfoundEntity, InaccessibleEntity
from ....models import get_full_name
from ....notification.notificator import Notificator
from ....schemas import CreatingComment, UpdatingComment

router = APIRouter()


@router.get(
    '/cp/stories/{story_id}/comments/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingComment],
    name="Получить все комментарии к истории",
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
    tags=["Административная панель / Комментарии"]
)
@router.get(
    '/stories/{story_id}/comments/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingComment],
    name="Получить все комментарии к истории",
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
    tags=["Мобильное приложение / Комментарии"]
)
def get_comments_by_story(
        story_id: int = Field(...,title="Идентификатор истории"),
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
):
    story = crud.story.get_by_id(db, story_id)

    if story is None:
        raise UnfoundEntity(num=2, message="История не найдена")

    data, paginator = crud.comment.get_story_comments(story=story, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.comment.get_comment(db, datum, current_user)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/stories/{story_id}/comments/',
    response_model=schemas.SingleEntityResponse[schemas.GettingComment],
    name="Добавить комментарий к истории",
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
    tags=["Мобильное приложение / Комментарии"]
)
def comment_story(
        data: CreatingComment,
        story_id: int = Field(...,title="Идентификатор истории"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
):
    story = crud.story.get_by_id(db, story_id)

    if story is None:
        raise UnfoundEntity(num=2, message="История не найдена")

    data = crud.comment.comment_story(db,story=story,user=current_user,obj_in=data)

    notificator.notify(
        title=f'Пользователь {get_full_name(current_user)} оставил комментарий',
        recipient=story.user,
        text=data.text,
        icon=current_user.avatar,
        db=db,
        link=f'krasnodar://story?id={story_id}'
    )

    return schemas.SingleEntityResponse(
        data=getters.comment.get_comment(db, data, current_user),
    )


@router.put(
    '/comments/{comment_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingComment],
    name="Изменить комментарий к истории",
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
    tags=["Мобильное приложение / Комментарии"]
)
def edit_comment(
        data: UpdatingComment,
        comment_id: int = Field(..., title="Идентификатор комментария"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_active_user),
):
    comment = crud.comment.get_by_id(db, comment_id)

    if comment is None:
        raise UnfoundEntity(num=1, message="Коментарий не найден")

    if comment.user != current_user and not current_user.is_superuser:
        raise InaccessibleEntity(num=1,message='Этот комментарий нельзя редактировать')

    data = crud.comment.update(db, db_obj=comment, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.comment.get_comment(db, data, current_user),
    )


@router.delete(
    '/comments/{comment_id}/',
    response_model=schemas.OkResponse,
    name="Удалить комментарий к истории",
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
    tags=["Мобильное приложение / Комментарии"]
)
def delete_comment(
        comment_id: int = Field(..., title="Идентификатор комментария"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_active_user),
):
    comment = crud.comment.get_by_id(db, comment_id)

    if comment is None:
        raise UnfoundEntity(num=1, message="Коментарий не найден")


    if comment.user != current_user and not current_user.is_superuser:
        raise InaccessibleEntity(num=1,message='Этот кормментарий нельзя удалить')
    user = comment.user
    if user.rating != 0:
        user.rating -= 1
    db.add(user)
    db.commit()
    crud.comment.remove(db, id=comment.id)

    return schemas.OkResponse()




@router.delete(
    '/cp/comments/{comment_id}/',
    response_model=schemas.OkResponse,
    name="Удалить комментарий к истории",
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
    tags=["Административная панель / Комментарии"]
)
def delete_comment(
        comment_id: int = Field(..., title="Идентификатор комментария"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_active_superuser),
):
    comment = crud.comment.get_by_id(db, comment_id)

    if comment is None:
        raise UnfoundEntity(num=1, message="Коментарий не найден")


    if comment.user != current_user and not current_user.is_superuser:
        raise InaccessibleEntity(num=1,message='Этот кормментарий нельзя удалить')
    user = comment.user
    if user.rating != 0:
        user.rating -= 1
    db.add(user)
    db.commit()
    crud.comment.remove(db, id=comment.id)

    return schemas.OkResponse()
