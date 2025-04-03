import asyncio
import json
import logging
import os.path
import uuid
from io import BytesIO
from typing import Any, List, Optional
import datetime

import boto3
from redis.client import Redis
from starlette.responses import StreamingResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.api import deps
from app.api.deps import get_db, get_current_active_user, get_bucket_name, get_s3_client, get_current_active_support
from app.exceptions import InaccessibleEntity, UnprocessableEntity, UnfoundEntity
from app.models import User, get_full_name
from app.notification.notificator import Notificator
from app.schemas.response import Meta, OkResponse, ListOfEntityResponse, SingleEntityResponse
from botocore.client import BaseClient
from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.params import File, Path, Header
from pydantic import Field, BaseModel
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session
from starlette.requests import Request

from otter_mini import crud_chat
from otter_mini.getters import get_contacting, get_chat, get_message
from otter_mini.schemas import GettingChat, GettingContacting, CreatingContacting, CreatingServiceChat, \
    CreatingGroupChat, NameBody, MembersBody, GettingMember, CreatingPersonalChat, GettingMessageWithParent, \
    CreatingMessageWithParent, MessagesBody, GettingAttachment


router = APIRouter()



@router.post(
    '/contactings/',
    response_model=SingleEntityResponse[GettingContacting],
    name="Сообщить о проблеме с регистрацией",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def create_contacting(
        db: Session = Depends(get_db),
        data: CreatingContacting = Body(...),

):
    contacting = crud_chat.chat.create_contacting(db=db, data=data)
    return SingleEntityResponse(data=get_contacting(contacting, db=db, user=None))


@router.get(
    '/cp/contactings/',
    response_model=ListOfEntityResponse[GettingContacting],
    name="Получить сообщения о проблеме с регистрацией",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"]
)
def create_contacting(
        db: Session = Depends(get_db),
        is_processed: Optional[bool] = Query(None, title="Обработано"),
        user_id: Optional[int] = Query(None, title="Идентификатор пользователя"),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: Optional[User] = Depends(get_current_active_support),
):
    data, paginator = crud_chat.chat.get_contactings(db,is_processed=is_processed, user_id=user_id,page=page)
    return ListOfEntityResponse(
        data=[
            get_contacting(contacting, db=db, user=current_user)
            for contacting
            in data
        ],
        meta=Meta(paginator=paginator)

    )

@router.put(
    '/cp/contactings/{contacting_id}/processed/',
    response_model=SingleEntityResponse[GettingContacting],
    name="Обработать сообщение о проблеме с регистрацией",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"]
)
def create_contacting(
        db: Session = Depends(get_db),
        contacting_id: int = Path(..., title="Идентификатор"),
        current_user: Optional[User] = Depends(get_current_active_support),
):
    contacting = crud_chat.chat.get_contacting(db, contacting_id)
    if contacting is None:
        raise UnfoundEntity(num=2, message="Сообщение не найдено")
    contacting =crud_chat.chat.process_contacting(db=db, contacting=contacting, user=current_user)
    return SingleEntityResponse(data=get_contacting(contacting, db=db, user=current_user))


@router.get(
    '/users/me/chats/',
    response_model=ListOfEntityResponse[GettingChat],
    name="Получить все чаты текущего пользователя",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def get_chats(
        db: Session = Depends(get_db),
        page: Optional[int] = Query(1, title="Номер страницы"),
        current_user: User = Depends(get_current_active_user),
        types: Optional[List[str]] = Query(None),
        subtypes: Optional[List[str]] = Query(None)
):
    data, paginator = crud_chat.chat.get_chat_for_user(db, user=current_user, page=page, types=types, subtypes=subtypes)
    return ListOfEntityResponse(
        data=data, meta=Meta(paginator=paginator)
    )


@router.get(
    '/users/me/chats/{chat_id}/',
    response_model=SingleEntityResponse[GettingChat],
    name="Получить чат по идентификатору",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def get_chats(
        db: Session = Depends(get_db),
        chat_id: int = Path(..., title="Идентификатор"),
        current_user: User = Depends(get_current_active_user),
):
    member = crud_chat.chat.find_member(db, chat_id, current_user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав читать этот чат")

    return SingleEntityResponse(
        data=crud_chat.get_chat(member, db, current_user)
    )


@router.post(
    path='/users/me/chats/attachments/',
    name="Загрузить вложение",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"],
    response_model=ListOfEntityResponse[GettingAttachment]
)
def load_attachments(
        db: Session = Depends(get_db),
        bucket_name=Depends(get_bucket_name),
        s3_client=Depends(get_s3_client),
        files: List[UploadFile] = File(...),
        user: User = Depends(get_current_active_user)
):
    data = crud_chat.chat.upload_attachments(db=db, data=files, user=user, bucket_name=bucket_name, s3_client=s3_client)
    return ListOfEntityResponse(data=data)


@router.post(
    '/users/me/chats/service/',
    response_model=SingleEntityResponse[GettingChat],
    name="Начать чат с тех поддержкой",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def create_service_chat(
        db: Session = Depends(get_db),
        data: CreatingServiceChat = Body(...),
        user: User = Depends(get_current_active_user)
):
    return SingleEntityResponse(data=crud_chat.chat.create_service_chat(db=db, data=data, user=user))


@router.post(
    '/users/me/chats/group/',
    response_model=SingleEntityResponse[GettingChat],
    name="Начать групповой чат",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def create_group_chat(
        db: Session = Depends(get_db),
        data: CreatingGroupChat = Body(...),
        user: User = Depends(get_current_active_user)
):
    return SingleEntityResponse(data=crud_chat.chat.create_group_chat(db=db, data=data, user=user))



@router.post(
    '/users/me/chats/personal/',
    response_model=SingleEntityResponse[GettingChat],
    name="Начать или продолжить чат c пользователем",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def create_personal_chat(
        db: Session = Depends(get_db),
        data: CreatingPersonalChat = Body(...),
        current_user: User = Depends(get_current_active_user)
):
    print("payload= ", data.json())
    second_user = db.query(User).get(data.user_id)
    if second_user is None:
        raise UnfoundEntity(message="Пользователь не найден", num=1)
    data=crud_chat.chat.create_personal_chat(
        db=db,
        current_user=current_user,
        second_user=second_user
    )
    print("response= ", data.json())
    return SingleEntityResponse(
        data=data
    )


@router.post(
    '/users/me/chats/{chat_id}/cover/',
    response_model=SingleEntityResponse[GettingChat],
    name="Изменить обложку чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        cover: UploadFile = File(...),
        user: User = Depends(get_current_active_user),
        bucket_name=Depends(get_bucket_name),
        s3_client=Depends(get_s3_client),
):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав редактировать этот чат")

    return SingleEntityResponse(data=crud_chat.chat.change_cover(db, member, cover, user, bucket_name, s3_client, ))


@router.post(
    '/users/me/chats/{chat_id}/name/',
    response_model=SingleEntityResponse[GettingChat],
    name="Изменить название чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        name_body: NameBody = Body(...),
        user: User = Depends(get_current_active_user),

):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав редактировать этот чат")

    return SingleEntityResponse(data=crud_chat.chat.change_name(db, member, name_body.name, user))


@router.post(
    '/users/me/chats/{chat_id}/members/',
    response_model=SingleEntityResponse[GettingChat],
    name="Добавить участников чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        members_body: MembersBody = Body(...),
        user: User = Depends(get_current_active_user),

):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав редактировать этот чат")
    if member.chat.type_ != 'group':
        raise UnprocessableEntity(message="Это не групповой чат")
    crud_chat.chat.add_members(db, member, members_body.members)
    return SingleEntityResponse(data=get_chat(member, db, user))


@router.get(
    '/users/me/chats/{chat_id}/members/',
    response_model=ListOfEntityResponse[GettingMember],
    name="Получить участников чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        page: Optional[int] = None,

):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав редактировать этот чат")
    data, paginator = crud_chat.chat.get_chat_members(db, member, page)
    return ListOfEntityResponse(data=data, paginator=paginator)


@router.delete(
    '/users/me/chats/{chat_id}/members/',
    response_model=SingleEntityResponse[GettingChat],
    name="Исключить участников чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        members_ids: Optional[List[int]] = Query(None),
        user: User = Depends(get_current_active_user),

):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав редактировать этот чат")
    # if member.chat.type_ != 'group':
    #     raise UnprocessableEntity(message="Это не групповой чат")
    old_ids = members_ids if members_ids else []
    crud_chat.chat.remove_members(db, member, old_ids)
    return SingleEntityResponse(data=get_chat(member, db, user))


@router.get(
    '/users/me/chats/{chat_id}/messages/',
    response_model=ListOfEntityResponse[GettingMessageWithParent],
    name="Получить сообщения чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(..., description="ID чата"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        start_id: Optional[int] = Query(None, description="ID последнего сообщения"),
        with_equals: Optional[bool] = Query(None, description="Включать ли сообщение с id равным start_id"),
        limit: Optional[int] = Query(None,description="Количество сообщений"),
        mode: Optional[str] = Query(None, description="Направление выборки.\n  Допустимые значения\n  `before` - выбирает сообщения до start_id\n  `after` - выбирает сообщения после start_id"),
        sorting: Optional[str] = Query(None, description="Сортировка сообщений.\n  Допустимые значения\n  `old` - старые сообщения вверху\n `new` - новые сообщения вверху"),
        timestamp: Optional[int] = Query(
            None,
            title="Отметка времени, с которой получить сообщения",
            description="Отметка времени, с которой получить сообщения"
        ),
):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав читать этот чат")
    data = crud_chat.chat.get_messages(db, member, start_id, limit, mode, sorting, with_equals, timestamp)
    return ListOfEntityResponse(data=data, paginator=None)


@router.post(
    '/users/me/chats/{chat_id}/messages/',
    response_model=SingleEntityResponse[GettingMessageWithParent],
    name="Отправить сообщение в чат",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        data: CreatingMessageWithParent = Body(...),
        notificator: Notificator = Depends(deps.get_notificator),
        redis_instance = Depends(deps.get_redis),

):
    print("chat id = ", chat_id)
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав читать этот чат")
    data = crud_chat.chat.send_message(db, member, data)
    members = [item for item in member.chat.members]
    # for item in members:
    #     if item.user_id != user.id:
    #         notificator.notify(
    #             db=db,
    #             recipient=item.user,
    #             title=item.chat_name or get_full_name(user),
    #             text=data.body or "Файл",
    #             icon=item.chat_cover or user.avatar,
    #             link=f'portugal://chat/?id={chat_id}'
    #         )
    #     payload = json.dumps(
    #         {
    #             'chat': item.chat.id,
    #             'message': data.dict()
    #         }
    #     )

    #     redis_instance.publish(
    #         f'chat-{item.user_id}',
    #         payload
    #     )

    return SingleEntityResponse(data=data, paginator=None)


@router.post(
    '/users/me/chats/{chat_id}/messages/read/',
    response_model=OkResponse,
    name="Отметить сообщения чата как прочитанные",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        data: MessagesBody = Body(...),

):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав читать этот чат")
    crud_chat.chat.read_messages(db, member, data)
    return OkResponse()


@router.delete(
    '/users/me/chats/{chat_id}/messages/',
    response_model=OkResponse,
    name="Удалить сообщения чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
        ids: Optional[List[int]] = Query(None),
        for_all: Optional[bool] = None,
):
    member = crud_chat.chat.find_member(db, chat_id, user)
    if member is None:
        raise InaccessibleEntity(message="У вас нет прав читать этот чат")
    if ids is None:
        ids = []
    if for_all is None:
        for_all = False
    crud_chat.chat.delete_messages(db, member, ids, for_all)
    return OkResponse()


@router.websocket("/ws/chats/messages/")
async def websocket_endpoint(
        websocket: WebSocket,
        db: Session = Depends(deps.get_db),
        token: str = Query(...),
        redis_instance: Redis = Depends(deps.get_redis),
):
    await websocket.accept()
    if not token:
        # await websocket.close()
        raise InaccessibleEntity()
    try:
        current_user = deps.get_current_user(
            db=db,
            token=token
        )
    except Exception:

        raise InaccessibleEntity()
    current_user = deps.get_current_user(
        db=db,
        token=token
    )
    db.close()
    pubsub = redis_instance.pubsub()
    pubsub.subscribe(f'chat-{current_user.id}')
    print(f'web socket connected for {current_user.id}')
    try:
        while True:
            data = pubsub.get_message(timeout=1, ignore_subscribe_messages=True)
            if data is not None:
                logging.info(type(data['data']))
                await websocket.send_text(data['data'].decode())
            else:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    await websocket.send_text(data)
                except asyncio.TimeoutError:
                    pass

    except WebSocketDisconnect:
        logging.info('WebSocket disconnected')
    finally:
        await pubsub.unsubscribe(f'chat-{current_user.id}')
        await pubsub.close()
        await redis_instance.close()




@router.get(
    '/cp/chats/services/',
    response_model=ListOfEntityResponse[GettingChat],
    name="Получить чаты тех поддержки",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"]
)
def get_chats(
        db: Session = Depends(get_db),
        page: Optional[int] = Query(None, title="Номер страницы"),
        current_user: User = Depends(get_current_active_support),
        subtypes: Optional[List[str]] = Query(None)
):
    data, paginator = crud_chat.chat.get_service_chats(db, user=current_user, page=page, subtypes=subtypes)
    return ListOfEntityResponse(
        data=data, meta=Meta(paginator=paginator)
    )


@router.get(
    '/cp/chats/{chat_id}/messages/',
    response_model=ListOfEntityResponse[GettingMessageWithParent],
    name="Получить сообщения чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(..., description="ID чата"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_support),
        start_id: Optional[int] = Query(None, description="ID последнего сообщения"),
        with_equals: Optional[bool] = Query(None, description="Включать ли сообщение с id равным start_id"),
        limit: Optional[int] = Query(None,description="Количество сообщений"),
        mode: Optional[str] = Query(None, description="Направление выборки.\n  Допустимые значения\n  `before` - выбирает сообщения до start_id\n  `after` - выбирает сообщения после start_id"),
        sorting: Optional[str] = Query(None, description="Сортировка сообщений.\n  Допустимые значения\n  `old` - старые сообщения вверху\n `new` - новые сообщения вверху"),

):

    data = crud_chat.chat.get_messages_of_chat_for_admin(
        db,
        chat_id=chat_id,
        user=user,
        start_id=start_id,
        limit=limit,
        mode=mode,
        sorting=sorting,
        with_equals=with_equals
    )
    return ListOfEntityResponse(data=data, paginator=None)


@router.post(
    '/cp/chats/{chat_id}/messages/',
    response_model=SingleEntityResponse[GettingMessageWithParent],
    name="Отправить сообщение в чат",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_support),
        data: CreatingMessageWithParent = Body(...),
        notificator: Notificator = Depends(deps.get_notificator),
        redis_instance = Depends(deps.get_redis),

):
    member = crud_chat.chat.find_tech_member(db, chat_id)

    data = crud_chat.chat.send_message(db, member, data, user=user)
    members = [item for item in member.chat.members]
    # for item in members:
    #     notificator.notify(
    #         db=db,
    #         recipient=item.user,
    #         title=item.chat_name,
    #         text=data.body,
    #         icon=item.chat_cover
    #     )
    #     payload = json.dumps(
    #         {
    #             'chat': item.chat.id,
    #             'message': data.dict()
    #         }
    #     )

    #     logging.info(
    #         redis_instance.publish(
    #             f'chat-{item.user_id}',
    #             payload
    #         )
    #     )

    return SingleEntityResponse(data=data, paginator=None)


@router.post(
    '/cp/chats/{chat_id}/messages/read/',
    response_model=OkResponse,
    name="Отметить сообщения чата как прочитанные",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"]
)
def change_group_cover(
        chat_id: int = Path(...),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_support),
        data: MessagesBody = Body(...),

):
    member = crud_chat.chat.find_tech_member(db, chat_id)
    crud_chat.chat.read_messages(db, member, data)
    return OkResponse()


@router.post(
    path='/cp/chats/attachments/',
    name="Загрузить вложение",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Панель управления / Чаты"],
    response_model=ListOfEntityResponse[GettingAttachment]
)
def load_attachments(
        db: Session = Depends(get_db),
        bucket_name=Depends(get_bucket_name),
        s3_client=Depends(get_s3_client),
        files: List[UploadFile] = File(...),
        user: User = Depends(get_current_active_support)
):
    data = crud_chat.chat.upload_attachments(db=db, data=files, user=user, bucket_name=bucket_name, s3_client=s3_client)
    return ListOfEntityResponse(data=data)

@router.get(
    '/users/me/chats/messages/unread/',
    name="Получить сообщения чата",
    responses={
        400: {
            'model': OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': OkResponse,
            'description': 'Отказанно в доступе'
        },
        404: {
            'model': OkResponse,
            'description': 'Пользователь не найден'
        }
    },
    tags=["Мобильное приложение / Чаты"]
)
def change_group_cover(

        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),

):
    data = crud_chat.chat.get_unread_count(db=db,user_id=user.id)
    return SingleEntityResponse(data={'count':data}, paginator=None)
