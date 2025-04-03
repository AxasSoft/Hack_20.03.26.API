import datetime
from io import BytesIO
from typing import List, Optional

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Header
from fastapi.params import File, Path
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import StreamingResponse

from app import crud, models, schemas, getters
from app.api import deps
from app.core.config import settings
from app.schemas.response import Meta
from ....exceptions import UnprocessableEntity, UnfoundEntity
from ....notification.notificator import Notificator
from ....schemas import GettingStat, SubscribeBody
import logging


from app.utils.cache import Cache

router = APIRouter()


@router.get(
    '/cp/users/export/',
    name="Экспортировать данные пользователей",
    tags=['Административная панель / Пользователи'],
)

def export_users(
        db: Session = Depends(deps.get_db),
):
    data = crud.user.export(db)
    export_media_type = 'text/csv'

    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')

    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}-{dt}.csv".format(file_name='users',dt=now)
    }
    return StreamingResponse(BytesIO(data), headers=export_headers, media_type=export_media_type)


@router.get(
    '/cp/users/me/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    tags=['Административная панель / Профиль'],
    name="Получить профиль текущего пользователя",
    responses={
        401: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не прошёл авторизацию'
        }
    }
)
@router.get(
    '/users/me/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Получить профиль текущего пользователя",
    tags=['Мобильное приложение / Профиль'],
    responses={
        401: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не прошёл авторизацию'
        }
    }
)
def get_current_user(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    x_real_ip: Optional[str] = Header(None),
    accept_language: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_firebase_token: Optional[str] = Header(None),
    cache: Cache = Depends(deps.get_cache_sing),
):
    def user_me():
        crud.user._handle_device(
                db=db,
                owner=current_user,
                host=request.client.host,
                x_real_ip=x_real_ip,
                accept_language=accept_language,
                user_agent=user_agent,
                x_firebase_token=x_firebase_token
        )
        return schemas.SingleEntityResponse(
            data=getters.user.get_user(db, current_user,current_user,)
        )

    key_tuple = ('user_me', f"user_me - {current_user.id}")
    data, from_cache = cache.behind_cache(key_tuple, user_me, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data


@router.put(
    '/cp/users/me/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить текущего пользователя",
    tags=['Административная панель / Профиль'],
    description="Любые поля запроса могут быть опущены. Измененены будут только переданные поля",
    responses={
        401: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не прошёл авторизацию'
        },
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
@router.put(
    '/users/me/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить текущего пользователя",
    description="Любые поля запроса могут быть опущены. Измененены будут только переданные поля",
    tags=['Мобильное приложение / Профиль'],
    responses={
        401: {
            'model': schemas.OkResponse,
            'description': 'Пользователь не прошёл авторизацию'
        },
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def edit_user(
    data: schemas.UpdatingUser,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {current_user.id}")
    cache.delete(key_tuple_user)

    d = data.dict(exclude_unset=True)
    if 'category_id' in d:
        category = crud.crud_category.category.get_by_id(db=db,id=d['category_id'])
        if category is None:
            raise UnfoundEntity(message='Категория не найдена')

    user = crud.user.update(
        db=db,
        db_obj=current_user,
        obj_in=data
    )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db, user, user)
    )


@router.put(
    '/cp/users/me/password/',
    response_model=schemas.OkResponse,
    name="Изменить пароль",
    description="Изменяет пароль",
    tags=['Административная панель / Профиль'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def change_password(
       data: schemas.PasswordBody,
       db: Session = Depends(deps.get_db),
       current_user: models.User = Depends(deps.get_current_active_user),
       cache: Cache = Depends(deps.get_cache_sing),
):
    key_tuple_user = ('user_me', f"user_me - {current_user.id}")
    cache.delete(key_tuple_user)

    result = crud.user.change_password(db=db, email=current_user.email,new_password=data.password)

    if result == -1:
        raise UnprocessableEntity(
            message="Пользователь не найден"
        )

    return schemas.OkResponse()


@router.post(
    '/cp/users/me/avatar/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить аватар",
    description="Изменить аватар. Передайте пустое значения для сброса аватара",
    tags=['Административная панель / Профиль'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
@router.post(
    '/users/me/avatar/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить аватар",
    description="Изменить аватар. Передайте пустое значения для сброса аватара",
    tags=['Мобильное приложение / Профиль'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def edit_avatar(
        new_avatar: Optional[UploadFile] = File(None),
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {user.id}")
    cache.delete(key_tuple_user)

    crud.user.s3_client = s3_client
    crud.user.s3_bucket_name = s3_bucket_name

    result = crud.user.change_avatar(db, user=user, new_avatar=new_avatar)

    if not result:
        raise UnprocessableEntity(
            message="Не удалось обновить аватар",
            description="Не удалось обновить аватар",
            num=1
        )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db, user,user)
    )


@router.post(
    '/cp/users/me/profile-cover/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить обложку",
    description="Изменить обложку. Передайте пустое значения для сброса обложки",
    tags=['Административная панель / Профиль'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
@router.post(
    '/users/me/profile-cover/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить обложку",
    description="Изменить обложку. Передайте пустое значения для сброса аватара",
    tags=['Мобильное приложение / Профиль'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def edit_profile_cover(
        new_profile_cover: Optional[UploadFile] = File(None),
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_sing),
):
    key_tuple_user = ('user_me', f"user_me - {user.id}")
    cache.delete(key_tuple_user)

    crud.user.s3_client = s3_client
    crud.user.s3_bucket_name = s3_bucket_name

    result = crud.user.change_profile_cover(db, user=user, new_profile_cover=new_profile_cover)

    if not result:
        raise UnprocessableEntity(
            message="Не удалось обновить обложку",
            description="Не удалось обновить обложку",
            num=1
        )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db, user,user)
    )


@router.get(
    '/users/exists/',
    response_model=schemas.SingleEntityResponse[schemas.ExistsBody],
    name="Проверить существавание пользователя",
    description="Проверить, существует ли пользователь с таким адресом электронной почты",
    tags=['Мобильное приложение / Профиль'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def user_exists(
        email: str = Query(...),
        db: Session = Depends(deps.get_db),
):

    data = crud.user.exists(db=db, email=email)

    return schemas.SingleEntityResponse(
        data=schemas.ExistsBody(
            exists=data
        )
    )



@router.get(
    '/cp/users/{user_id}/devices/',
    response_model=schemas.ListOfEntityResponse[schemas.Device],
    tags=['Административная панель / Пользователи'],
    name="Устройства пользователя",
    description="Получить список устройств, с которых пользователь входил в приложение или регистрировался в приложении",
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        }
    }
)
def get_devices_by_admin(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
        user_id: Optional[int] = Path(..., title="Идентификатор пользователя"),
        page: Optional[int] = Query(1, title="Номер страницы")
):
    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")
    data,paginator = crud.user.get_user_devices(db, user=getting_user, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.user.get_device(
                datum
            )
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.get(
    '/cp/users/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUserShortAdminInfo],
    name="Найти пользователей",
    description="Найти пользователей по айди, адресу электронной почты и имени",
    tags=['Административная панель / Пользователи'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        }
    }
)
def search_user(
        search: Optional[str] = Query(None,title="Поисковый запрос"),
        sorting: Optional[str] = Query(
            None,
            title='Поле для сортировки',
        ),
        is_superuser: Optional[bool] = Query(None, title='Является ли пользователь суперпользователем'),
        is_active: Optional[bool] = Query(None, title='Является ли аккаунт пользователя активированным'),
        in_whitelist: Optional[bool] = Query(None),
        in_blacklist: Optional[bool] = Query(None),
        region: Optional[str] = Query(None),
        page: Optional[int] = Query(1, title="Номер страницы"),
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
        is_editor: Optional[bool] = Query(None, title='Является ли пользователь редактором'),
        is_support: Optional[bool] = Query(None, title='Является ли пользователь агентом поддержки'),
):
    data, paginator = crud.user.search_users(
        db,
        search=search,
        page=page,
        is_superuser=is_superuser,
        is_active=is_active,
        sorting=sorting,
        in_blacklist=in_blacklist,
        in_whitelist=in_whitelist,
        region=region,
        is_editor=is_editor,
        is_support=is_support,
    )

    return schemas.ListOfEntityResponse(
        data=[
            getters.user.get_user_short_admin_info(datum)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.get(
    '/users/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUserShortAdminInfo],
    name="Найти пользователей",
    description="Найти пользователей по айди, адресу электронной почты и имени",
    tags=['Мобильное приложение / Пользователи'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def search_user(
        search: Optional[str] = Query(None,title="Поисковый запрос"),
        region: Optional[str] = Query(None),
        location: Optional[str] = Query(None),
        rating_from: Optional[float] = Query(None),
        rating_to: Optional[float] = Query(None),
        category_id: Optional[int] = Query(None),
        current_lat: Optional[float] = Query(None),
        current_lon: Optional[float] = Query(None),
        distance: Optional[float] = Query(None),
        is_business: Optional[bool] = Query(None),
        page: Optional[int] = Query(1, title="Номер страницы"),
        category_ids: Optional[List[int]] = Query(None),
        db: Session = Depends(deps.get_db),
):
    data, paginator = crud.user.search_users_by_user(
        db,
        search=search,
        region=region,
        location=location,
        rating_from=rating_from,
        rating_to=rating_to,
        category_id=category_id,
        current_lat=current_lat,
        current_lon=current_lon,
        distance=distance,
        is_business=is_business,
        category_ids=category_ids,
        page=page,
    )

    return schemas.ListOfEntityResponse(
        data=[
            getters.user.get_user_short_admin_info(datum)
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.get(
    '/cp/users/{user_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUserWithAdminInfo],
    name="Получить пользователя",
    description="Получить пользователя",
    tags=['Административная панель / Пользователи'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        },
        404:{
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    }
)
@router.get(
    '/cp/users/{user_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUserWithAdminInfo],
    name="Получить пользователя",
    description="Получить пользователя",
    tags=['Административная панель / Пользователи'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        },
        404:{
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    }
)
def get_user_by_id(
        user_id: Optional[int] = Path(..., title="Идентификатор полльзователя"),
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
):
    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")

    return schemas.SingleEntityResponse(
        data=getters.user.get_user_with_admin_info(db, getting_user)
    )


@router.get(
    '/users/{user_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Получить пользователя",
    description="Получить пользователя",
    tags=['Мобильное приложение / Пользователи'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        404:{
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    }
)
def get_user_by_id(
        user_id: Optional[int] = Path(..., title="Идентификатор пользователя"),
        db: Session = Depends(deps.get_db),
        current_user: Optional[models.User] = Depends(deps.get_optional_current_user),
        cache: Cache = Depends(deps.get_cache_sing),
):
    def get_user_id():
        getting_user = crud.user.get_by_id(db, user_id)
        if getting_user is None:
            raise UnfoundEntity(message="Пользователь не найден")

        return schemas.SingleEntityResponse(
            data=getters.user.get_user(db, db_obj=getting_user, db_user=current_user)
        )

    key_tuple = ('user_me', f"user_me - {user_id}")
    data, from_cache = cache.behind_cache(key_tuple, get_user_id, ttl=7200)
    
    if from_cache:
        logging.info("From the cache")
    else:
        logging.info("From the database")

    return data



@router.put(
    '/cp/users/{user_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить пользователя",
    description="Изменить пользователя",
    tags=['Административная панель / Пользователи'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        },
        404:{
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    }
)
def edit_user_by_admin(
        data: schemas.UpdatingUserByAdmin,
        user_id: int = Path(..., title="Идентификатор полльзователя"),
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
        cache: Cache = Depends(deps.get_cache_sing),
):
    key_tuple_user = ('user_me', f"user_me - {user_id}")
    cache.delete(key_tuple_user)
    cache.delete_by_prefix('stories_by_user')

    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")

    d = data.dict(exclude_unset=True)
    if 'category_id' in d:
        category = crud.crud_category.category.get_by_id(db=db,id=d['category_id'])
        if category is None:
            raise UnfoundEntity(message='Категория не найдена')


    getting_user = crud.user.update_user_by_admin(
        db=db,
        user=getting_user,
        new_data=data
    )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db, getting_user,None)
    )


@router.post(
    '/cp/users/{user_id}/avatar/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить аватар",
    description="Изменить аватар. Передайте пустое значения для сброса аватара",
    tags=['Административная панель / Пользователи'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def edit_avatar_by_admin(
        new_avatar: Optional[UploadFile] = File(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        user_id: int = Path(..., title="Идентификатор полльзователя"),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {user_id}")
    cache.delete(key_tuple_user)


    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")

    crud.user.s3_client = s3_client
    crud.user.s3_bucket_name = s3_bucket_name

    result = crud.user.change_avatar(db, user=getting_user, new_avatar=new_avatar)

    if not result:
        raise UnprocessableEntity(
            message="Не удалось обновить аватар",
            description="Не удалось обновить аватар",
            num=1
        )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db, getting_user, None)
    )


@router.post(
    '/cp/users/{user_id}/profile-cover/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить обложку",
    description="Изменить обложку. Передайте пустое значения для сброса обложки",
    tags=['Административная панель / Пользователи'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def edit_profile_cover_by_admin(
        new_profile_cover: Optional[UploadFile] = File(None),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        user_id: int = Path(..., title="Идентификатор полльзователя"),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {user_id}")
    cache.delete(key_tuple_user)

    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")

    crud.user.s3_client = s3_client
    crud.user.s3_bucket_name = s3_bucket_name

    result = crud.user.change_profile_cover(db, user=getting_user, new_profile_cover=new_profile_cover)

    if not result:
        raise UnprocessableEntity(
            message="Не удалось обновить аватар",
            description="Не удалось обновить аватар",
            num=1
        )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db, getting_user, None)
    )





@router.delete(
    '/cp/users/me/',
    response_model=schemas.OkResponse,
    name="Удалить аккаунт",
    description="Удалить аккаунт",
    tags=['Административная панель / Профиль'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        }
    }
)
@router.delete(
    '/users/me/',
    response_model=schemas.OkResponse,
    name="Удалить аккаунт",
    description="Удалить аккаунт",
    tags=['Мобильное приложение / Профиль'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        }
    }
)
def delete_profile(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_user),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {user.id}")
    cache.delete(key_tuple_user)
    cache.delete_by_prefix('stories_by_user')
    cache.delete_by_prefix('chat_by_user')

    crud.user.delete_user(
        db=db,
        user=user,
    )

    return schemas.OkResponse()

@router.delete(
    '/cp/users/{user_id}/',
    response_model=schemas.OkResponse,
    name="Удалить пользователя",
    description="Удалить пользователя",
    tags=['Административная панель / Пользователи'],
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
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизорван'
        },
        404:{
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    }
)
def delete_user_by_admin(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_superuser),
        user_id: int = Path(..., title="Идентификатор полльзователя"),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {user_id}")
    cache.delete_by_prefix('chat_by_user')
    cache.delete_by_prefix('stories_by_user')
    cache.delete(key_tuple_user)
    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")

    crud.user.delete_user(
        db=db,
        user=getting_user,
    )

    return schemas.OkResponse()


@router.put(
    '/users/{user_id}/block/',
    response_model=schemas.OkResponse,
    name="Заблокировать или разблокировать пользователя",
    tags=['Мобильное приложение / Пользователи'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    }
)
def block_user(
        data: schemas.user.BlockBody,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        user_id: int = Path(..., title="Идентификатор пользователя"),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_user = ('user_me', f"user_me - {user_id}")
    key_tuple_current_user = ('user_me', f"user_me - {current_user.id}")
    cache.delete(key_tuple_user)
    cache.delete(key_tuple_current_user)
    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользователь не найден")
    crud.user.block_user(db=db, subject=current_user, object_=getting_user, block=data.block)

    return schemas.OkResponse()



@router.post(
    '/cp/push-notifications/',
    response_model=schemas.response.SingleEntityResponse[schemas.user.GettingPushNotification],
    name="Создать рассылку уведомлений",
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
    tags=['Административная панель / Пользователи']
)
def broadcast(
        data: schemas.user.CreatingPushNotification,
        db: Session = Depends(deps.get_db),
        current_user: models.user.User = Depends(deps.get_current_user),
        notificator: Notificator = Depends(deps.get_notificator)
):
    push_notification = crud.crud_user.user.push_notify(
        db=db,
        notificator=notificator,
        push=data
    )

    return schemas.response.SingleEntityResponse(
        data=getters.get_push_notification(push_notification=push_notification)
    )


@router.get(
    '/cp/push-notifications/',
    response_model=schemas.response.ListOfEntityResponse[schemas.user.GettingPushNotification],
    name="Получить рассылки уведомлений",
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
    tags=['Административная панель / Пользователи']
)
def get_push_history(
        page: Optional[int] = Query(None),
        current_user: models.user.User = Depends(deps.get_current_active_superuser),
        db: Session = Depends(deps.get_db),
):

    data, paginator = crud.crud_user.user.get_push_history(
        db=db,
        page=page,
    )
    return schemas.response.ListOfEntityResponse(
        data=[getters.get_push_notification(push_notification=push) for push in data],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.get(
    '/users/me/notifications/',
    response_model=schemas.response.ListOfEntityResponse[schemas.GettingNotification],
    name="Получить историю уведомлений",
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
    tags=["Мобильное приложение / Общее / Профиль"]
)
def get_notifications(
        page: Optional[int] = Query(None),
        current_user: models.user.User = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
):

    data, paginator = crud.crud_user.user.get_notifications(
        db=db,
        page=page,
        user=current_user,
    )
    return schemas.response.ListOfEntityResponse(
        data=[getters.get_notification(db=db, notification=notification) for notification in data],
        meta=schemas.response.Meta(paginator=paginator)
    )


@router.put(
    '/notifications/{notification_id}/is-read/',
    response_model=schemas.response.SingleEntityResponse[schemas.GettingNotification],
    name="Пометить уведомление как прочитанное или непрочитанное",
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
    tags=["Мобильное приложение / Общее / Профиль"]
)
def mark_notification(
        data: schemas.IsReadBody,
        current_user: models.user.User = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db),
        notification_id: int = Path(..., title='Идентификатор уведомления')
):

    notification = db.query(models.Notification).get(notification_id)
    notification = crud.crud_user.user.mark_notification_as_read(db=db, notification=notification, is_read=data.is_read)

    return schemas.response.SingleEntityResponse(
        data=getters.get_notification(db=db, notification=notification)
    )



@router.get(
    '/cp/stats/',
    response_model=schemas.response.SingleEntityResponse[GettingStat],
    name="Получить статистику",
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
    tags=["Административная панель / Статистика"]
)
def get_notifications(
        current_user: models.user.User = Depends(deps.get_current_active_superuser),
        db: Session = Depends(deps.get_db),
):

    data = crud.crud_user.user.stat(
        db=db,
    )
    return schemas.response.SingleEntityResponse(
        data=data,
        meta=schemas.response.Meta(paginator=None)
    )


@router.put(
    '/users/{user_id}/in_subscriptions/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    name="Изменить статус подписки",
    description="Изменить статус подписки на указанного пользователя",
    tags=['Мобильное приложение / Пользователи'],
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданны невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        404:{
            'model': schemas.OkResponse,
            'description': 'Пользователь не найден'
        }
    }
)
def subscribe(
        new_value: SubscribeBody,
        user_id: Optional[int] = Path(..., title="Идентификатор пользователя"),
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        notificator: Notificator = Depends(deps.get_notificator),
        cache: Cache = Depends(deps.get_cache_list),
):
    key_tuple_current_user = ('user_me', f"user_me - {current_user.id}")
    key_tuple_user = ('user_me', f"user_me - {user_id}")
    cache.delete(key_tuple_current_user)
    cache.delete(key_tuple_user)

    getting_user = crud.user.get_by_id(db, user_id)
    if getting_user is None:
        raise UnfoundEntity(message="Пользоsватель не найден")

    crud.user.subscribe(db,subject=current_user,object_=getting_user,new_value=new_value.subscribe)
    if new_value.subscribe:
        notificator.notify(
            db,
            getting_user,
            f'Пользователь {" ".join(name for name in (current_user.first_name, current_user.patronymic, current_user.last_name) if name is not None) } подписался на вас',
            'Новая подписка',
            icon=current_user.avatar,
            link=f'krasnodar://user?id={current_user.id}'
        )

    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db,db_obj=getting_user,db_user=current_user)
    )


@router.get(
    '/users/me/subscriptions/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUser],
    tags=['Мобильное приложение / Профиль'],
    name="Подписки",
    description="Получить список подписок",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказано в доступе'
        },
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизован'
        }
    }
)
def get_subscriptions(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
        page: Optional[int] = Query(None),
):
    data, paginator = crud.user.get_subscriptions(db, user=user, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.get_user(
                db=db,
                db_obj=datum.object_,
                db_user=user
            )
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.get(
    '/users/me/subscribers/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingUser],
    tags=['Мобильное приложение / Профиль'],
    name="Подписки",
    description="Получить список подписчиков",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказано в доступе'
        },
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизован'
        }
    }
)
def get_subscriptions(
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
        page: Optional[int] = Query(None),
):
    data, paginator = crud.user.get_subscribers(db, user=user, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.get_user(
                db=db,
                db_obj=datum.subject,
                db_user=user
            )
            for datum
            in data
        ],
        meta=Meta(paginator=paginator)
    )


@router.post(
    '/cp/users/',
    response_model=schemas.SingleEntityResponse[schemas.GettingUser],
    tags=['Административная панель / Пользователи'],
    name="Создать пользователя",
    description="Создать пользователя",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        },
        403: {
            'model': schemas.OkResponse,
            'description': 'Отказано в доступе'
        },
        401: {
            'model': schemas.OkResponse,
            'description': 'Не авторизован'
        }
    }
)
def create_user(
        user: schemas.user.CreatingUser,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    user = crud.crud_user.user.create(db=db, obj_in=user)
    return schemas.SingleEntityResponse(
        data=getters.user.get_user(db,db_obj=user,db_user=current_user)
    )

@router.get(
    '/cp/test-push/',
    name="push test",
    tags=['Административная панель / Пользователи'],
)

def test_push(
    user_id: int,
    db: Session = Depends(deps.get_db),
    notificator: Notificator = Depends(deps.get_notificator),
    user: models.User = Depends(deps.get_current_active_superuser),
):
    user = crud.user.get_by_id(db, user_id)
    notificator.notify(
                db, recipient=user, text='test_body', title='test_title', icon=None, link=f'krasnodar://chat?id={str(89)}&last_message={str(48)}',
            )

@router.post(
    '/cp/test-push-many/',
    name="push test many",
    tags=['Административная панель / Пользователи'],
)
def test_push_many(
    user_ids: List[int],
    db: Session = Depends(deps.get_db),
    notificator: Notificator = Depends(deps.get_notificator),
    user: models.User = Depends(deps.get_current_active_superuser),
):
    user_list = []
    for i in user_ids:
        user_list.append(crud.user.get_by_id(db, i))
    notificator.notify_many(
                db, recipients=user_list, text='test_body', title='test_title', icon=None, link=''
            )






# @router.get(
#     '/users/delete/all/test',
#     response_model=schemas.OkResponse,
#     tags=['Мобильное приложение / Профиль'],
#     name="УДАЛЕНИЕ ПО ФАСТУ",
#     description="Получить список подписчиков",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданы невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         },
#         403: {
#             'model': schemas.OkResponse,
#             'description': 'Отказано в доступе'
#         },
#         401: {
#             'model': schemas.OkResponse,
#             'description': 'Не авторизован'
#         }
#     }
# )
# def get_subscriptions(
#         db: Session = Depends(deps.get_db),
#         page: Optional[int] = Query(None),
# ):
#     for i in range(70, 370):
#         try:
#             getting_user = crud.user.get_by_id(db, i)
#             if not getting_user:
#                 print(f"Пользователь с ID {i} не найден. Пропускаем.")
#                 continue  

#             crud.user.delete_user(
#                 db=db,
#                 user=getting_user,
#             )

#         except Exception as e:
#             print(f"Ошибка при обработке пользователя с ID {i}: {e}")
#             continue

#     return schemas.OkResponse()
 
