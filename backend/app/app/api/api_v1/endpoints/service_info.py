from typing import Optional

from botocore.client import BaseClient
from fastapi import APIRouter, Depends, UploadFile
from fastapi.params import File, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnprocessableEntity, UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/service-infos/',
    tags=['Административная панель / Служебные информационные блоки'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingServiceInfo],
    name="Получить все доступные служебные информационные блоки",

)
@router.get(
    '/service-infos/',
    response_model=schemas.ListOfEntityResponse[schemas.GettingServiceInfo],
    name="Получить все доступные служебные информационные блоки",
    tags=['Мобильное приложение / Служебные информационные блоки'],
)
def get_all(
        db: Session = Depends(deps.get_db)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.service_info.get_service_info(info)
            for info
            in crud.service_info.get_multi(db=db, page=None)[0]
        ]
    )


@router.get(
    '/cp/service-infos/{slug}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingServiceInfo],
    name="Получить служебный информационный блок",
    description="Изменить информационный блок",
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
            'description': 'Информационный блок не найдена'
        }
    },
    tags=["Административная панель / Служебные информационные блоки"]
)
@router.get(
    '/service-infos/{slug}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingServiceInfo],
    name="Получить служебный информационный блок",
    description="Изменить информационный блок",
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
            'description': 'Информационный блок не найдена'
        }
    },
    tags=["Мобильное приложение / Служебные информационные блоки"]
)
def get_info(
        db: Session = Depends(deps.get_db),
        slug: str = Path(...)
):

    info = crud.service_info.get_by_slug(db, slug)
    if info is None:
        raise UnfoundEntity(
            message="Информационный блок не найден"
        )


    return schemas.SingleEntityResponse(
        data=getters.service_info.get_service_info(info)
    )


@router.post(
    '/cp/service-infos/',
    response_model=schemas.SingleEntityResponse[schemas.GettingServiceInfo],
    name="Добавить служебный информационный блок",
    description="Добавить новый служебный информационный блок",
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
    tags=["Административная панель / Служебные информационные блоки"]
)
def create_info(
        data: schemas.CreatingServiceInfo,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    info = crud.service_info.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.service_info.get_service_info(info)
    )


@router.put(
    '/cp/service-infos/{slug}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingServiceInfo],
    name="Изменить служебный информационный блок",
    description="Изменить информационный блок",
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
            'description': 'Информационный блок не найдена'
        }
    },
    tags=["Административная панель / Служебные информационные блоки"]
)
def edit_info(
        data: schemas.UpdatingServiceInfo,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        slug: str = Path(...)
):

    info = crud.service_info.get_by_slug(db, slug)
    if info is None:
        raise UnfoundEntity(
            message="Информационный блок не найден"
        )
    info = crud.service_info.update(db, db_obj=info, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.service_info.get_service_info(info)
    )


# @router.delete(
#     '/cp/service-infos/{slug}/',
#     response_model=schemas.OkResponse,
#     name="Удалить информационный блок",
#     description="Удалить информационный блок",
#     responses={
#         400: {
#             'model': schemas.OkResponse,
#             'description': 'Переданны невалидные данные'
#         },
#         422: {
#             'model': schemas.OkResponse,
#             'description': 'Переданные некорректные данные'
#         },
#         403: {
#             'model': schemas.OkResponse,
#             'description': 'Отказанно в доступе'
#         },
#         404: {
#             'model': schemas.OkResponse,
#             'description': 'Информационный блок не найден'
#         }
#     },
#     tags=["Административная панель / Служебные информационные блоки"]
# )
# def delete_info(
#         db: Session = Depends(deps.get_db),
#         current_user: models.User = Depends(deps.get_current_active_superuser),
#         slug: str = Path(...)
# ):
#
#     info = crud.service_info.get_by_slug(db, slug)
#     if info is None:
#         raise UnfoundEntity(
#             message="Информационный блок не найден"
#         )
#
#     crud.service_info.remove(db=db, id=info.id)
#
#     return schemas.OkResponse()


@router.post(
    '/cp/service-infos/{slug}/image/',
    response_model=schemas.SingleEntityResponse[schemas.GettingServiceInfo],
    name="Изменить изображение",
    tags=['Административная панель / Служебные информационные блоки'],
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
def edit_image_by_admin(
        new_image: Optional[UploadFile] = File(None),
        db: Session = Depends(deps.get_db),
        current_ser: models.Info = Depends(deps.get_current_active_superuser),
        slug: str = Path(...),
        s3_client: BaseClient = Depends(deps.get_s3_client),
        s3_bucket_name: str = Depends(deps.get_bucket_name),
):

    getting_info = crud.service_info.get_by_slug(db, slug)
    if getting_info is None:
        raise UnfoundEntity(message="Информационный блок не найден")

    crud.service_info.s3_client = s3_client
    crud.service_info.s3_bucket_name = s3_bucket_name

    result = crud.service_info.change_image(db, info=getting_info, new_image=new_image)

    if not result:
        raise UnprocessableEntity(
            message="Не удалось обновить изображение",
            description="Не удалось обновить изображение",
            num=1
        )

    return schemas.SingleEntityResponse(
        data=getters.service_info.get_service_info(getting_info)
    )


