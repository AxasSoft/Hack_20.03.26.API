from io import BytesIO
import datetime
from io import BytesIO
from typing import List, Optional

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, Query, UploadFile, Form
from fastapi.params import File, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app import crud, models, schemas, getters
from app.api import deps
from app.schemas.response import Meta
from ....enums.mod_status import ModStatus
from ....exceptions import UnfoundEntity, InaccessibleEntity
from ....models import Offer, get_full_name
from ....models.order import Stage
from ....notification.notificator import Notificator
from ....schemas import CreatingOrder, UpdatingOrder, BlockBody

from ....exceptions import UnfoundEntity, UnprocessableEntity

router = APIRouter()



@router.get(
    "/ads/promo/all/",
    tags=["Мобильное приложение / Промо Объявления"],
    name="Получить все промо",
    response_model=schemas.response.ListOfEntityResponse[schemas.promo_order.GettingPromoOrder],
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
)
def get_all_promos(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    page: int = Query(None),
):
    return _get_all(db, page)


@router.get(
    "/cp/ads/promo/all/",
    tags=["Панель Управления / Промо Объявления"],
    name="Получить все промо",
    response_model=schemas.response.ListOfEntityResponse[schemas.promo_order.GettingPromoOrder],
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
)
def get_all_promos_admin(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    page: int = Query(None),
):
    return _get_all(db, page)


def _get_all(
    db: Session,
    page: int  = None,
):
    data, paginator = crud.crud_promo_order.promo_order.get_page(
        db=db, page=page
    )

    return schemas.response.ListOfEntityResponse(
        data=[getters.promo_order.get_promo_order(db=db,db_obj=promo) for promo in data],
        meta=schemas.response.Meta(paginator=paginator),
        errors=[],
    )


@router.get(
    "/ads/promo/{promo_id}/",
    tags=["Мобильное приложение / Промо Объявления"],
    name="Получить Статью по идентификатору",
    response_model=schemas.response.SingleEntityResponse[schemas.promo_order.GettingPromoOrder],
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
)
@router.get(
    "/cp/ads/promo/{promo_id}/",
    tags=["Панель Управления / Промо Объявления"],
    name="Получить Статью по идентификатору",
    response_model=schemas.response.SingleEntityResponse[schemas.promo_order.GettingPromoOrder],
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
)
def get_promo_by_id(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    promo_id: int = Path(...),
):
    promo = crud.crud_promo_order.promo_order.get_by_id(db=db, id=promo_id)
    if promo is None:
        raise UnfoundEntity(message="Промо не найден", num=1)

    return schemas.response.SingleEntityResponse(
        data=getters.promo_order.get_promo_order(db=db, db_obj=promo)
    )


@router.post(
    "/cp/ads/promo/",
    tags=["Панель Управления / Промо Объявления"],
    name="Создать Промо к объявлениям",
    response_model=schemas.response.SingleEntityResponse[schemas.promo_order.GettingPromoOrder],
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
)
def create_promo(
    data: schemas.promo_order.CreatingPromoOrder,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
   
    if data.order_id is not None:
        product = crud.order.get_by_id(db, data.order_id)
        if product is None:
            raise UnfoundEntity(message="Продукта не найдена")
    if data.subcategory_id is not None:
        sub_categ = crud.crud_subcategory.subcategory.get_by_id(db=db, id=data.subcategory_id)
        if sub_categ is None:
            raise UnfoundEntity(message="Подкатегория не найдена")    
    if data.info_id is not None:
        info = crud.crud_info.info.get_by_id(db=db, id=data.info_id)
        if info is None:
            raise UnfoundEntity(message="Информационного блока не найдено")    

    promo = crud.crud_promo_order.promo_order.create(
        db=db, obj_in=data
    )

    return schemas.response.SingleEntityResponse(
        data=getters.promo_order.get_promo_order(db=db, db_obj=promo)
    )


@router.put(
    "/cp/ads/promo/{promo_id}",
    tags=["Панель Управления / Промо Объявления"],
    name="Изменить промо",
    response_model=schemas.response.SingleEntityResponse[schemas.promo_order.GettingPromoOrder],
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
)
def edit_promo(
    data: schemas.promo_order.UpdatingPromoOrder,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    promo_id: int = Path(...),
):
    if data.order_id is not None:
        product = crud.order.get_by_id(db, data.order_id)
        if product is None:
            raise UnfoundEntity(message="Продукта не найдена")
    if data.subcategory_id is not None:
        sub_categ = crud.crud_subcategory.subcategory.get_by_id(db=db, id=data.subcategory_id)
        if sub_categ is None:
            raise UnfoundEntity(message="Подкатегория не найдена")    
    if data.info_id is not None:
        info = crud.crud_info.info.get_by_id(db=db, id=data.info_id)
        if info is None:
            raise UnfoundEntity(message="Информационного блока не найдено")    
    
    promo = crud.crud_promo_order.promo_order.get_by_id(db=db, id=promo_id)

    if promo is None:
        raise UnfoundEntity(message="Промо не найден", num=1)

    promo = crud.crud_promo_order.promo_order.update(db=db, db_obj=promo, obj_in=data)

    return schemas.response.SingleEntityResponse(
         data=getters.promo_order.get_promo_order(db=db, db_obj=promo)
    )


@router.delete(
    "/cp/ads/promo/{promo_id}",
    tags=["Панель Управления / Промо Объявления"],
    name="удалить Промо",
    response_model=schemas.response.OkResponse,
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
)
def delete_promo_adm(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    promo_id: int = Path(...),
):
    promo = crud.crud_promo_order.promo_order.get_by_id(db=db, id=promo_id)
    if promo is None:
        raise UnfoundEntity(message="Промо не найден", num=1)
    crud.crud_promo_order.promo_order.remove(db=db, id=promo_id)

    return schemas.response.OkResponse()


@router.post(
    "/cp/ads/promo/{promo_id}/cover/",
    response_model=schemas.response.SingleEntityResponse[schemas.promo_order.GettingPromoOrder],
    name="Изменить обложку",
    description="Изменить обложку. Передайте пустое значения для сброса обложки",
    tags=["Панель Управления / Промо Объявления"],
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
)
def edit_cover(
    new_cover: UploadFile = File(None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    promo_id: int = Path(...),
    s3_client: BaseClient = Depends(deps.get_s3_client),
    s3_bucket_name: str = Depends(deps.get_bucket_name),
):

    promo = crud.crud_promo_order.promo_order.get_by_id(db=db, id=promo_id)
    if promo is None:
        raise UnfoundEntity(message="Промо не найден", num=1)

    crud.crud_promo_order.promo_order.s3_client = s3_client
    crud.crud_promo_order.promo_order.s3_bucket_name = s3_bucket_name

    result = crud.crud_promo_order.promo_order.add_promo_cover(
        db,
        obj=promo,
        image=new_cover,
    )

    if result is None:
        raise UnprocessableEntity(
            message="Не удалось обновить обложку",
            description="Не удалось обновить обложку",
            num=1,
        )

    return schemas.response.SingleEntityResponse(
         data=getters.promo_order.get_promo_order(db=db, db_obj=result)
    )
