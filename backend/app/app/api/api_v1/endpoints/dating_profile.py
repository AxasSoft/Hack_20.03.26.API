from typing import List, Optional
import logging
from app import crud, getters, models, schemas
from app.api import deps
from app.core.config import settings
from app.schemas.response import Meta
from botocore.client import BaseClient
from fastapi import APIRouter, Body, Depends, File, Form, Header, Query, UploadFile
from fastapi.params import File, Path
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import StreamingResponse
from pydantic import conint
from ....exceptions import UnfoundEntity, UnprocessableEntity
from ....notification.notificator import Notificator
from ....schemas import GettingStat, SubscribeBody

router = APIRouter()

# @router.post(
#     '/cp/dating/profile/create/',
#     response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
#     tags=['Административная панель / Профиль знакомств'],
#     name="Создать профиль знакомств",
#     responses={
#         401: {
#             'model': schemas.OkResponse,
#             'description': 'Пользователь не прошёл авторизацию'
#         }
#     }
# )
# def get_current_super_user(
#     dating_profile: schemas.dating_profile.CreatingDatingProfile,
#     request: Request,
#     db: Session = Depends(deps.get_db),
#     current_user: models.User = Depends(deps.get_current_active_user),
# ):
#     existing_profile = crud.dating_profile.get_by_user_id(db, user_id=current_user.id)
#     if existing_profile:
#         raise UnfoundEntity(
#             message="Профиль знакомств уже существует"
#         )

#     new_profile = crud.dating_profile.create_with_user(db, obj_in=dating_profile, user=current_user)

#     return schemas.SingleEntityResponse(
#         data=getters.dating_profile.get_dating_profile(new_profile)
#     )


@router.post(
    "/dating/profile/create/",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    name="Создать профиль знакомств текущему пользователю",
    description='''  
    поле     
    relationship_type   
    ```
    friendly_communication = 0
    romantic_relationships = 1
    any_relationship = 2
    ```
            ''',
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        }
    },
)
def create_current_user_profile(
    dating_profile: schemas.dating_profile.CreatingDatingProfile,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    existing_profile  = current_user.dating_profile
    if existing_profile:
        raise UnfoundEntity(message="Профиль знакомств уже существует")

    new_profile = crud.dating_profile.create_with_user(
        db, obj_in=dating_profile, user=current_user
    )

    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(db=db, dating_profile=new_profile)
    )


@router.post(
    "/dating/profile/add/images/",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    name="Добавить фото в профиль знакомств текущему пользователю",
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        }
    },
)
def add_current_profile_images(
    images: List[UploadFile] = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    s3_client: BaseClient = Depends(deps.get_s3_client),
    s3_bucket_name: str = Depends(deps.get_bucket_name),
):
    existing_profile  = current_user.dating_profile
    if existing_profile is None:
        raise UnfoundEntity(message="Профиль знакомств не существует")
    crud.dating_profile.s3_client = s3_client
    crud.dating_profile.s3_bucket_name = s3_bucket_name

    try:
        crud.dating_profile.add_dating_profile_photo(
        db, images=images, db_obj=existing_profile
    )
    except Exception:
         raise UnfoundEntity(message="Не удалось загрузить картинку")

    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(db=db, dating_profile=existing_profile)
    )


@router.delete(
    "/dating/profile/del/{image_id}/",
    response_model=schemas.response.SingleEntityResponse[schemas.GettingDatingProfile],
    name="Удалить изображение профиля знакомств",
    responses={
        400: {
            "model": schemas.response.OkResponse,
            "description": "Переданы невалидные данные",
        },
        422: {
            "model": schemas.response.OkResponse,
            "description": "Переданы некорректные данные",
        },
        403: {
            "model": schemas.response.OkResponse,
            "description": "Отказано в доступе",
        },
    },
    tags=["Мобильное приложение / Профиль знакомств"],
)
def delete_image(
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
    s3_client: BaseClient = Depends(deps.get_s3_client),
    s3_bucket_name: str = Depends(deps.get_bucket_name),
    image_id: int = Path(..., title="Идентификатор объявления"),
):
    existing_profile  = current_user.dating_profile
    if existing_profile is None:
        raise UnfoundEntity(message="Профиля знакомств не существует")
    image = crud.dating_profile.get_image_by_id(db=db, id=image_id)
    if image is None:
        raise UnfoundEntity(num=1, message="Картинка не найдена")

    crud.crud_order.order.s3_client = s3_client
    crud.crud_order.order.s3_bucket_name = s3_bucket_name
    crud.dating_profile.delete_image(db=db, image=image)
    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(db=db, dating_profile=existing_profile)
    )


@router.get(
    "/dating/profile/",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    name="Получить профиль знакомств текущего пользователя",
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        }
    },
)
def get_current_user(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    existing_profile = current_user.dating_profile
    if existing_profile is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(
            db, existing_profile
        )
    )


@router.get(
    "/dating/profile/{profile_id}",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    name="Получить профиль знакомств по индетификатору",
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        }
    },
)
def get_current_user(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    profile_id: int = Path(..., description="Идентификатор фильма")

):
    existing_profile = crud.crud_dating_profile.dating_profile.get_by_id(db=db, id=profile_id)
    if existing_profile is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(
            db=db, dating_profile=existing_profile
        )
    )



@router.put(
    "/dating/profile/edit/",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    description='''Любые поля запроса могут быть опущены. Измененены будут только переданные поля   
    поле - relationship_type   
    ```
    friendly_communication = 0
    romantic_relationships = 1
    any_relationship = 2
    ```
            ''',
    name="Изменить профиль знакомств текущего пользователя",
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        },
        400: {
            "model": schemas.OkResponse,
            "description": "Переданны невалидные данные",
        },
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
    },
)
def edit_user(
    data: schemas.UpdatingDatingProfile,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    dating_profile_user = current_user.dating_profile
    if dating_profile_user is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
    update_dating_profile = crud.dating_profile.update_dating_profile(
        db=db, user=current_user, db_obj=dating_profile_user, obj_in=data
    )

    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(db=db, dating_profile=update_dating_profile)
    )


@router.delete(
    "/dating/profile/",
    response_model=schemas.OkResponse,
    name="Удалить профиль знакомств текущего пользователя",
    description="Удалить профиль знакомств текущего пользователя",
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        400: {
            "model": schemas.OkResponse,
            "description": "Переданны невалидные данные",
        },
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
        403: {"model": schemas.OkResponse, "description": "Отказанно в доступе"},
        401: {"model": schemas.OkResponse, "description": "Не авторизорван"},
    },
)
def delete_profile(
    db: Session = Depends(deps.get_db),
    user: models.User = Depends(deps.get_current_user),
):
    crud.dating_profile.delete_dating_profile(db=db, user=user)

    return schemas.OkResponse()


# Вывод всех анкет для знакомств
@router.get(
    "/dating/profile/search/",
    response_model=schemas.ListOfEntityResponse[schemas.GettingDatingProfile],
    description='''Получить список профилей знакомств   
    gender_filter
    ```
    male = 0   
    female = 1   
    ```
    поле relationship_type   
    ```   
    friendly_communication = 0   
    romantic_relationships = 1   
    any_relationship = 2   
    ```   
    Поле rate_weight   
    ```
0: 1.0,  # Высокая оценка   

1: -1.0, # Низкая оценка   

2: 0.3,  # Средняя оценка   

3: 0.6   # Оценка среднего уровня   
    ```
            ''',
    name="Получить профили знакомств",
    tags=["Мобильное приложение / Профиль знакомств"],
)
def get_ssearch_dating_profiles(
    db: Session = Depends(deps.get_db),
    page: Optional[int] = Query(1, title="Номер страницы"),
    current_user: models.User = Depends(deps.get_current_user),
    gender_filter: Optional[conint(ge=0, le=1)] = Query(None, title="Фильтр по полу"),
    age_filter_min: Optional[int] = None,
    age_filter_max: Optional[int] = None,
    relationship_type_filter: Optional[conint(ge=0, le=2)] = Query(None, title="Фильтр по полу"),
):
    
    dating_profile_user  = current_user.dating_profile
    if dating_profile_user is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
    
    data, paginator = crud.dating_profile.get_search_dating_profiles(db, user=current_user, 
                                                                    page=page, 
                                                                    gender_filter=gender_filter, 
                                                                    age_filter_min=age_filter_min,
                                                                    age_filter_max=age_filter_max,
                                                                    relationship_type_filter=relationship_type_filter
                                                                    )

    return schemas.ListOfEntityResponse(
        data=[
            getters.dating_profile.get_dating_profile(
                db, item
            )
            for item in data
        ], meta=Meta(paginator=paginator)
    )


@router.post(
    "/dating/profile/like/",
    response_model=schemas.OkResponse,
    description='''`like` - True(лайк), False(Диздайк)   
                    liker_estimate_type = от 0 до 3   

                    `0: 1.0,  # Высокая оценка`     
                    `1: -1.0, # Низкая оценка`   
                    `2: 0.3,  # Средняя оценка`   
                    `3: 0.6   # Оценка среднего уровня`   
                ''',
    name="Поставить профилю нравится или не нравится",
    tags=["Мобильное приложение / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        },
        400: {
            "model": schemas.OkResponse,
            "description": "Переданны невалидные данные",
        },
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
    },
)
def add_like_dating_profile(
    data: schemas.LikeDisLikeDatingProfile,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    
    dating_profile_user  = current_user.dating_profile
    if dating_profile_user is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")

    dating_profile = crud.dating_profile.get_by_id(
        db, id=data.profile_id
    )
    if dating_profile is None:
        raise UnfoundEntity(message="Профиль знакомств не найден")
    
    save_like_user = crud.dating_profile.save_like(db, user=current_user, data=data)

    return schemas.OkResponse()



@router.get(
    '/dating/profile/like/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingDatingProfileLike],
    name="Получить отметки нравится для текущего пользователя",
    tags=['Мобильное приложение / Профиль знакомств'],
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
def get_like_dating_profile(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    page: Optional[int] = Query(1, title="Номер страницы"),
):
    
    dating_profile_user  = current_user.dating_profile
    if dating_profile_user is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")

    like_dating_profile, paginator = crud.dating_profile.get_like_dating_profile(db, current_user=current_user, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.dating_profile.get_dating_profile_like_me(
                db=db,
                profile_like = item
            )
            for item in like_dating_profile    
        ], meta=Meta(paginator=paginator)
    )



@router.get(
    '/dating/profile/mutual/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingDatingProfileMutual],
    name="Получить взаимные отметки нравится для текущего пользователя",
    tags=['Мобильное приложение / Профиль знакомств'],
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
def get_mutual_dating_profile(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    page: Optional[int] = Query(1, title="Номер страницы"),
):
    
    dating_profile_user  = current_user.dating_profile
    if dating_profile_user is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")

    mutual_dating_profile, paginator = crud.dating_profile.get_mutual_dating_profile(db, current_user=current_user, page=page)

    return schemas.ListOfEntityResponse(
        data=[
            getters.dating_profile.get_dating_profile_mutual_me(
                db=db,
                profile_like = item
            )
            for item in mutual_dating_profile    
        ], meta=Meta(paginator=paginator)
    )



@router.put(
    "/cp/dating/profile/edit/{profile_id}/",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    description='''Любые поля запроса могут быть опущены. Измененены будут только переданные поля   
    поле - relationship_type   
    ```
    friendly_communication = 0
    romantic_relationships = 1
    any_relationship = 2
    ```
            ''',
    name="Изменить профиль знакомств польователя по индентификатору",
    tags=["Административная панель / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        },
        400: {
            "model": schemas.OkResponse,
            "description": "Переданны невалидные данные",
        },
        422: {
            "model": schemas.OkResponse,
            "description": "Переданные некорректные данные",
        },
    },
)
def edit_user(
    data: schemas.UpdatingDatingProfile,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    profile_id: int = Path(..., description="Идентификатор фильма")
):
    dating_profile_user = crud.dating_profile.get_by_id(
        db, id=profile_id
    )
    if dating_profile_user is None:
        raise UnfoundEntity(message="Профиль не найден")
    update_dating_profile = crud.dating_profile.update_dating_profile(
        db=db, user=dating_profile_user.user, db_obj=dating_profile_user, obj_in=data
    )

    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(db=db, dating_profile=update_dating_profile)
    )


@router.get(
    "/cp/dating/profile/{profile_id}/",
    response_model=schemas.SingleEntityResponse[schemas.GettingDatingProfile],
    name="Получить профиль знакомств по индетификатору",
    tags=["Административная панель / Профиль знакомств"],
    responses={
        401: {
            "model": schemas.OkResponse,
            "description": "Пользователь не прошёл авторизацию",
        }
    },
)
def get_current_user(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    profile_id: int = Path(..., description="Идентификатор фильма")

):
    existing_profile = crud.crud_dating_profile.dating_profile.get_by_id(db=db, id=profile_id)
    if existing_profile is None:
        raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
    return schemas.SingleEntityResponse(
        data=getters.dating_profile.get_dating_profile(
            db=db, dating_profile=existing_profile
        )
    )



@router.get(
    '/cp/dating/profile/test/rating/',
    response_model=None,
    name="test rating",
    tags=['Административная панель / Профиль знакомств'],
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
def get_test(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    try:
        crud.dating_profile._recalculate_weights()
    finally:
        db.close()

    return None



@router.get(
    '/cp/dating/fake/db',
    response_model=schemas.ListOfEntityResponse[schemas.GettingDatingProfile],
    name="fake database",
    tags=['Административная панель / Профиль знакомств'],
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
def get_fake(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    quantity: Optional[int] = Query(None, title=""),
):
    page = crud.dating_profile.fake_db(db=db, quantity=quantity)

    return None 

