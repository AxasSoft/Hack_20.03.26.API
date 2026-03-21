import datetime
import json
from typing import Optional, List

import logging

import asyncio
from app import crud, models, schemas, getters, enums
from app.api import deps
from app.notification.notificator import Notificator
from app.schemas.response import Meta
from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, WebSocket, Header, HTTPException, Body
from fastapi.params import Path, File, Form
from redis import Redis
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect
from pydantic import conint

from app.services.free4gpt.gpt_manager import gpt_manager
from ....core.connection_manager import ConnectionManager
from ....crud import CrudChat
from ....exceptions import UnfoundEntity, InaccessibleEntity
from ....getters import get_chat, get_message, get_attachment, get_message_with_parent, get_unread_messages_count
from ....models import get_full_name
from ....schemas import GettingChat, GettingMessage, SendingMessage, GettingAttachment, \
    OrderBy, MessagesList, CreatingMessageWithParent, GettingMessageWithParent, GettingCoutnUnRead

import logging


from app.utils.cache import Cache

router = APIRouter()
event_manager = ConnectionManager()
msg_manager = ConnectionManager()

@router.get(
    '/chats/',
    response_model=schemas.ListOfEntityResponse[GettingChat],
    name="Получить уже начатые чаты",
    description='''
    type_chat - Тип чата   
    ```
    personal = 0
    dating = 1
    order = 2
    neuro = 3
    ```''',
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
    },
    tags=["Мобильное приложение / Чаты"]
)
def get_active_chats(
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        type_chat: Optional[List[conint(ge=0, le=3)]] = Query(None, title="Типы Чата"),
        is_empty_chat: Optional[bool] = True,
        page: Optional[int] = Query(None),
        cache: Cache = Depends(deps.get_cache_list),
):

    def fatch_chat_all():
        crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)

        data, paginator = crud_chat.get_active_chats(
            db=db,
            current_user=current_user,
            page=page,
            type_chat=type_chat,
            is_empty_chat=is_empty_chat
        )

        return schemas.ListOfEntityResponse(
            data=[
                get_chat(db, datum, current_user)
                for datum
                in data
            ],
            meta=Meta(paginator=paginator)
        )

    key_tuple = ('chat_by_user', f"current_user - {current_user.id} - page - {page} - type_chat - {type_chat} - is_empty_chat - {is_empty_chat}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_chat_all, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.post(
    '/users/{user_id}/chats/',
    response_model=schemas.SingleEntityResponse[GettingChat],
    name="Начать или продолжить чат с пользователем или искусственным интеллектом",
    description='''
    type_chat - Тип чата   
    ```
    personal = 0
    dating = 1
    order = 2
    neuro = 3
    ```''',
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
    },
    tags=["Мобильное приложение / Чаты"]
)
async def init_chat(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        type_chat: conint(ge=0, le=3) = Query(..., title="Тип Чата"),
        cache: Cache = Depends(deps.get_cache_sing),
        user_id: int = Path(..., title="Идентификатор пользователя, с которым необходимо начать или продолжить диалог"),
):
    async def fatch_chat_user():
        user = crud.user.get_by_id(db=db, id=user_id)
        if user is None:
            raise UnfoundEntity('Собеседник не найден')
        crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
        chat, created = crud_chat.init_chat(db=db, initiator=current_user, recipient=user, type_chat=type_chat)
        if created and user_id:
            await event_manager.send_personal_message(
                json.dumps(
                    {
                        'event': 'starting',
                        'type': 'Chat',
                        'id': chat.id
                    }
                ),
                user_id
            )
        return schemas.SingleEntityResponse(
            data=get_chat(db=db, chat=chat, current_user=current_user)
        )
    key_tuple = ('chat_by_user', f"current_user - {current_user.id} - user_id - {user_id} - \
                 type_chat - {type_chat}")
    data, from_cache = await cache.behind_cache_asyc(key_tuple, fatch_chat_user, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data

@router.get(
    '/chats/{chat_id}/messages/',
    response_model=schemas.ListOfEntityResponse[GettingMessageWithParent],
    name="Получить сообщения чата",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
def get_messages_of_chat(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        chat_id: int = Path(..., title="Идентификатор чата",description="Идентификатор чата"),
        timestamp: Optional[int] = Query(
            None,
            title="Отметка време, с которой получить сообщения",
            description="Отметка време, с которой получить сообщения"
        ),
        count: int = Query(
            0,
            title='Количество получаемых сообщений',
            description="Передайте:\n   "
                        "0 -  для получения всех сообщений,\n  "
                        "отрицательное число - для получения некоторого количества сообщений до отметки времени,\n  "
                        "положительное число - для получения некоторго количества сообщений после отметки времени"
        ),
        order_by: str = Query(
            'asc',
            title="Порядок выдачи сообщений", description="`asc` - от старого к новому,\n  `desc` - от нового к старому"
        ),
        with_equal: bool = Query(False, title="Включая точное совпадение", description="Включая точное совпадение"),
        start_id: Optional[int] = Query(None, description="ID последнего сообщения"),
        mode: Optional[str] = Query(None, description="Направление выборки.\n  Допустимые значения\n  `before` - выбирает сообщения до start_id\n  `after` - выбирает сообщения после start_id"),
        # cache: Cache = Depends(deps.get_cache_list),
):
    # cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    chat = crud_chat.get_chat_by_id(db=db,id=chat_id)
    if chat is None:
        raise UnfoundEntity('Чат не найден')
    elif current_user not in (chat.recipient.user, chat.initiator.user):
        raise InaccessibleEntity('Недоступный чат')

    if timestamp is None:
        dt = datetime.datetime.utcnow()
    else:
        dt = datetime.datetime.utcfromtimestamp(timestamp)

    messages = crud_chat.get_messages(
        db=db,
        current_user=current_user,
        chat=chat,
        timestamp=dt,
        count=count,
        order_by=order_by,
        with_equal=with_equal,
        start_id=start_id,
        mode=mode,
    )

    return schemas.ListOfEntityResponse(
        data=[
            get_message_with_parent(db=db,message=message,user=current_user)
            for message
            in messages
        ]
    )


@router.post(
    '/chats/attachments/',
    response_model=schemas.SingleEntityResponse[GettingAttachment],
    name="Загрузить вложение",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
def load_attachment(
        file: UploadFile = File(None),
        note: str = Form(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    attachment = crud_chat.load_attachment(db=db, current_user=current_user,attachment=file,note=note)
    return schemas.SingleEntityResponse(
        data=get_attachment(
            attachment=attachment
        )
    )


@router.delete(
    '/chats/attachments/{attachments_id}/',
    response_model=schemas.OkResponse,
    name="удалить вложение",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
async def delete_attachment(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        attachments_id: int = Path(..., title="Идентификатор Вложение"),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    attachment = crud_chat.get_attachment_by_id(db, id=attachments_id)
    if attachment is None:
        raise UnfoundEntity('Вложение не найдено')
    
    result_delete = crud_chat.delete_attachment(db=db, attachment=attachment)
    if result_delete is False:
        raise InaccessibleEntity('Ошибка при удалении')

    return schemas.OkResponse()


@router.post(
    '/chats/{chat_id}/messages/',
    response_model=schemas.SingleEntityResponse[GettingMessageWithParent],
    name="Отправить сообщение в чат",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
async def send_message_in_chat(
        message: CreatingMessageWithParent,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        notificator: Notificator = Depends(deps.get_notificator),
        chat_id: int = Path(..., title="Идентификатор чата"),
        redis_instance: Redis = Depends(deps.get_redis),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    chat = crud_chat.get_chat_by_id(db=db,id=chat_id)
    if chat is None:
        raise UnfoundEntity('Чат не найден')
    if chat.type_chat == enums.type_chat.TypeChat.neuro:
        message = crud_chat.send_message(db=db, current_user=current_user, chat=chat, message=message)
        second_user = None
    else:
        if current_user == chat.recipient.user:
            second_user = chat.initiator.user
        elif current_user == chat.initiator.user:
            second_user = chat.recipient.user
        else:
            raise InaccessibleEntity('Недоступный чат')

        message = crud_chat.send_message(db=db,current_user=current_user,chat=chat, message=message)

        await event_manager.send_personal_message(
            json.dumps(
                {
                    'event': 'receive',
                    'type': 'Message',
                    'id': message.id
                }
            ),
            second_user.id
        )


        await msg_manager.send_personal_message(
            json.dumps(
                {
                    'chat': chat.id,
                    'message': get_message_with_parent(db=db, message=message, user=current_user).dict()
                }
            ),
            second_user.id
        )

    logging.info('start publishing')


    # Публикация сообщения в Redis
    if second_user:
        data = json.dumps(
            {
                'chat': chat.id,
                'message': get_message_with_parent(db=db, message=message, user=current_user).dict()
            }
        )

        logging.info(f'message for publication:{data}')
        published = redis_instance.publish(f'chat-{second_user.id}', data)
    else:
        data = json.dumps(
            {
                'chat': chat.id,
                'message_text': message.text,
                'user_id': current_user.id,
            }
            , ensure_ascii=False
        )

        logging.info(f'message for publication:{data}')
        published = redis_instance.publish(f'chat-neuro', data)
    # Логирование результата публикации
    logging.info(f'result of the publication:{published}')

    # Проверка, опубликовано ли сообщение
    if published == 0:
        logging.warning('not been published, there may be no subscribers to the channel')
    else:
        logging.info('The message was successfully published')


    logging.info('end publishing')

    if second_user:
        notificator.notify(
            db=db,
            recipient=second_user,
            text=message.text,
            title=get_full_name(message.sender.user),
            icon=current_user.avatar,
            chat=chat_id,
            link=f'krasnodar://chat?id={str(chat_id)}'
        )
    return schemas.SingleEntityResponse(
        data=get_message_with_parent(db=db, message=message, user=current_user)
    )


@router.delete(
    '/chats/messages/{message_id}/',
    response_model=schemas.OkResponse,
    name="удалить сообщение",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
async def delete_message(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        message_id: int = Path(..., title="Идентификатор сообщения"),
        # ids: Optional[List[int]] = Query(None),
        for_all: bool = Query(False),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    message = crud_chat.get_message_by_id(db,id=message_id)
    if message is None:
        raise UnfoundEntity('Сообщение не найдено')

    if message.sender.user != current_user:
        raise InaccessibleEntity('Нельзя удалить это сообщение')

    chat = message.sender.received_chat or message.sender.initiated_chat

    if current_user == chat.recipient.user:
        second_user = chat.initiator.user
    else:
        second_user = chat.recipient.user

    crud_chat.delete_message(db=db,message=message, current_user=current_user,for_all=for_all)
    if for_all:
        await event_manager.send_personal_message(
            json.dumps(
                {
                    'event': 'delete',
                    'type': 'Message',
                    'id': message_id
                }
            ),
            second_user.id
        )

    return schemas.OkResponse()



@router.websocket("/ws/chats/messages/")
async def websocket_endpoint(
        websocket: WebSocket,
        db: Session = Depends(deps.get_db),
        authorization: str = Header(...),
        redis_instance: Redis = Depends(deps.get_redis),
):
    logging.info('Start chat')
    try:
        current_user = deps.get_current_user(db=db, token=authorization)
        logging.info(f'Current user: {current_user.id}')
    except Exception as e:
        logging.info(f'Error get Current user: {e}')
        await websocket.close()
        return None

    await msg_manager.connect(websocket, current_user.id)
    logging.info(f'Connect is user: {current_user.id}')

    pubsub = redis_instance.pubsub()
    pubsub.subscribe(f'chat-{current_user.id}')
    logging.info(f'Subscribed to the channel: chat-{current_user.id}')

    try:
        while True:
            logging.info('Started websocket while')
            data = pubsub.get_message(timeout=1, ignore_subscribe_messages=True)
            if data is not None:
                logging.info(f'Received a message from Redis: {data}')
                logging.info(type(data['data']))
                await websocket.send_text(data['data'].decode())
                logging.info(f'A message has been sent to the client: {data["data"].decode()}')
            else:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    logging.info(f'A message has been received from the client:{data}')
                    logging.info(f'A message has been sent to the client: {data}')
                except asyncio.TimeoutError:
                    logging.info('Timeout for waiting for a message from the client')
                    pass

    except WebSocketDisconnect:
        logging.info('The client has disconnected')
        msg_manager.disconnect(websocket)
        logging.info('disconnect')
    finally:
        pubsub.unsubscribe(f'chat-{current_user.id}')
        logging.info(f'Unsubscribed from the channel: chat-{current_user.id}')
        pubsub.close()
        logging.info('Closed Pub/Sub')


@router.post(
    '/chats/messages/is_read/',
    response_model=schemas.OkResponse,
    name="Отметить сообщение как прочитаное",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
def mark_as_read(
        messages_ids: MessagesList,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    crud_chat.mark_read(db=db,message_ids=messages_ids.messages)
    return schemas.OkResponse()


# @router.websocket("/ws/chats/events/")
# async def websocket_endpoint(
#         websocket: WebSocket,
#         db: Session = Depends(deps.get_db),
#         authorization: str = Header(...),
# ):
#     try:
#         current_user = deps.get_current_user(db=db, token=authorization)
#     except Exception:
#         await websocket.close()
#         return None
#     await event_manager.connect(websocket, current_user.id)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             logging.info(msg_manager.active_connections)
#             logging.info(data)
#             await websocket.send_text(f"data")
#     except WebSocketDisconnect:
#         event_manager.disconnect(websocket)
#         logging.info('disconnect')




@router.get(
    '/users/me/chats/{chat_id}/',
    # response_model=SingleEntityResponse[GettingChat],
    response_model=schemas.SingleEntityResponse[GettingChat],
    name="Получить чат по идентификатору",
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
    tags=["Мобильное приложение / Чаты"]
)
def get_chats(
        db: Session = Depends(deps.get_db),
        chat_id: int = Path(..., title="Идентификатор"),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def fatch_chat_id():
        crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)

        data = crud_chat.get_chat_by_id(db=db, id=chat_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Чат не найден")

        return schemas.SingleEntityResponse(
            data=get_chat(chat=data, db=db, current_user=current_user)
        )

    key_tuple = ('chat_by_user', f"current_user - {current_user.id} - chat_id - {chat_id}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_chat_id, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data

    
@router.delete(
    '/users/me/chats/{chat_id}/members/',
    response_model=schemas.SingleEntityResponse[None],
    name="Исключить участников чата",
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
    },
    tags=["Мобильное приложение / Чаты"]
)
async def delete_message(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        chat_id: int = Path(..., title="Идентификатор чата"),
        for_all: bool = Query(False, title=""),
        cache: Cache = Depends(deps.get_cache_list),
):
    cache.delete_by_prefix('chat_by_user')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)

    member = crud_chat.find_member(db, chat_id, current_user)
    if member is None:
        raise InaccessibleEntity(message="Текущего пользователя в чате нет")
    chat = crud_chat.get_chat_by_id(db=db, id=chat_id)
    all_massage = crud_chat.get_messages(db=db, chat=chat, 
                                         count=0,
                                         current_user=current_user,
                                         timestamp=None)
    for mess in all_massage:
        crud_chat.delete_message(db=db, message=mess, 
                                 current_user=current_user, 
                                 for_all=for_all)
    crud_chat.remove_members(db, member)

    return schemas.SingleEntityResponse()


@router.get(
    '/users/me/chats/{type_chat_id}/count/messages',
    response_model=schemas.SingleEntityResponse[GettingCoutnUnRead],
    name="Получить колличество не прочитанных сообщений",
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
    tags=["Мобильное приложение / Чаты"]
)
def get_chats_coutn(
        db: Session = Depends(deps.get_db),
        type_chat_id: int = Path(..., title="Идентификатор чата"),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def fatch_coutn_un_read():
        crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)

        data = crud_chat.get_unread_messages_count(db=db, current_user=current_user, 
                                                    type_chat=type_chat_id)

        return schemas.SingleEntityResponse(
            data=get_unread_messages_count(obj=data)
        )

    key_tuple = ('chat_by_user', f"current_user - {current_user.id} - type_chat_id - {type_chat_id}")
    data, from_cache = cache.behind_cache(key_tuple, fatch_coutn_un_read, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.put(
    '/users/{user_id}/chats/blocking/',
    response_model=schemas.SingleEntityResponse[GettingChat],
    name="Заблокировать/разблокировать пользователя",
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
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def chat_blocking(
        blocking: bool = Body(...),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        user_id: int = Path(..., title="Идентификатор пользователя, с которым необходимо начать или продолжить диалог"),
        type_chat: conint(ge=0, le=2) = Query(..., title="Тип Чата"),
        cache: Cache = Depends(deps.get_cache_sing),
):
    user = crud.user.get_by_id(db=db, id=user_id)
    if user is None:
        raise UnfoundEntity('Собеседник не найден')
    crud_chat = CrudChat(s3_client=s3_client, s3_bucket_name=s3_bucket_name)
    chat, created = crud_chat.init_chat(db=db, initiator=current_user, recipient=user, type_chat=type_chat)
    chat = crud_chat.block_user(db=db, current_user=current_user, second_user=user, chat=chat, blocking=blocking)
    cache.delete_by_prefix('chat_by_user')

    return schemas.SingleEntityResponse(
        data=get_chat(db=db, chat=chat, current_user=current_user)
    )
