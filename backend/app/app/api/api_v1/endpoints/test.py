from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.params import Path, Header
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.requests import Request
from redis.client import Redis
from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta, OkResponse
from ....exceptions import UnprocessableEntity, UnfoundEntity, ListOfEntityError, InaccessibleEntity
from ....schemas import CreatingStory, UpdatingStory
from ....schemas.story import HugBody, HidingBody, IsFavoriteBody

from app.utils.cache import Cache

router = APIRouter()



@router.post(
    '/test/redis/',
    response_model=schemas.SingleEntityResponse[None],
    name="Тест Redis",
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
    tags=["Песочница / Тесты"]
)
def add_new_story(
        db: Session = Depends(deps.get_db),
        # current_user: models.User = Depends(deps.get_current_active_superuser),
        # user_id: int = Path(...,title="Идентификатор пользователя"),
        redis_instance: Redis = Depends(deps.get_redis),
):

    print(redis_instance)
    pubsub = redis_instance.pubsub()
    print(pubsub)
    pubsub.subscribe('chat-12')

    redis_instance.set('key', 'value')
    print('web socket connected for 122')

    return schemas.SingleEntityResponse()


@router.post(
    '/test/redis/chat/',
    response_model=schemas.SingleEntityResponse[None],
    name="Тест Redis Chat Canal",
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
    tags=["Песочница / Тесты"]
)
def add_new_story(
        db: Session = Depends(deps.get_db),
        redis_instance: Redis = Depends(deps.get_redis),
):


    # Создание объекта Pub/Sub
    pubsub = redis_instance.pubsub()

    # Подписка на канал
    pubsub.subscribe('chat-1')

    # Функция для обработки сообщений
    def handle_message(message):
        print(f"Received message: {message['data'].decode()}")

    # Запуск цикла для получения сообщений
    for message in pubsub.listen():
        if message['type'] == 'message':
            handle_message(message)

    return schemas.SingleEntityResponse()



@router.post(
    '/test/cash/delate/',
    response_model=schemas.SingleEntityResponse[None],
    name="cach test dell",
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
    tags=["Песочница / Тесты"]
)
def add_new_story(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        cache: Cache = Depends(deps.get_cache_list),
):

    cache.delete_by_prefix('stories_by_user')

    return schemas.SingleEntityResponse()