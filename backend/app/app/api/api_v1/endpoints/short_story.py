from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path, Header
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta, OkResponse
from ....exceptions import UnprocessableEntity, UnfoundEntity, ListOfEntityError, InaccessibleEntity
from ....schemas import CreatingStory, UpdatingStory
from ....schemas.story import HugBody, HidingBody, IsFavoriteBody
import logging


from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/short-stories/subscriptions/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUserStories],
    name="Получить short-истории подписок",
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
    tags=["Мобильное приложение / Истории"]
)
def get_short_stories_from_subscriptions(
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    def fatch_short_stories_subscriptions():
        data, paginator = crud.story.get_short_stories_from_subscriptions(
            db,
            page=page,
            current_user=current_user,
        )

        return schemas.ListOfEntityResponse(
            data=[
                getters.story.get_grouped_short_story(db, datum, current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )


    key_tuple = ('short_stories_by_user',
                 f"user_subscriptions - {current_user.id} - page - {page} - grouped_by_users")
    data, from_cache = cache.behind_cache(key_tuple, fatch_short_stories_subscriptions, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.get(
    '/short-stories/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUserStories],
    name="Получить все short-истории",
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
            'description': 'Пользователь, хештег или тема не найдены'
        }
    },
    tags=["Мобильное приложение / Истории"]
)
def get_short_stories(
        request: Request,
        db: Session = Depends(deps.get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
        x_real_ip: Optional[str] = Header(None),
        accept_language: Optional[str] = Header(None),
        user_agent: Optional[str] = Header(None),
        x_firebase_token: Optional[str] = Header(None),
        cache: Cache = Depends(deps.get_cache_list),

):
    def fatch_short_stories():
        data, paginator = crud.story.get_short_stories(
            db,
            page=page,
            current_user=current_user,
            host=request.client.host,
            x_real_ip=x_real_ip,
            accept_language=accept_language,
            user_agent=user_agent,
            x_firebase_token=x_firebase_token,
        )


        return schemas.ListOfEntityResponse(
            data=[
                getters.story.get_grouped_short_story(db, datum, current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )

    key_tuple = ('short_stories_by_user', f"user - {current_user.id} - page - \
                 {page} - grouped_by_users")
    data, from_cache = cache.behind_cache(key_tuple, fatch_short_stories, ttl=7200)

    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data
