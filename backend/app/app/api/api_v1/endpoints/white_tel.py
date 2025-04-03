import datetime
from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.params import Path
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app import crud, models, schemas, getters
from app.api import deps
from ....exceptions import UnfoundEntity

router = APIRouter()


@router.get(
    '/cp/white-tels/export/',
    name="Экспортировать данные белых номеров телефона",
    tags=['Административная панель / Белые номера телефонов'],
)

def export(
        db: Session = Depends(deps.get_db),
):
    data = crud.white_tel.export(db)
    export_media_type = 'text/csv'

    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')

    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}-{dt}.csv".format(file_name='white-tels',dt=now)
    }
    return StreamingResponse(BytesIO(data), headers=export_headers, media_type=export_media_type)


@router.get(
    '/cp/white-tels/',
    tags=['Административная панель / Белые номера телефонов'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingWhiteTel],
    name="Получить все доступные белые номера телефонов",

)
def get_all(
        db: Session = Depends(deps.get_db)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.white_tel.get_white_tel(white_tel)
            for white_tel
            in crud.white_tel.get_multi(db=db, page=None)[0]
        ]
    )


@router.post(
    '/cp/white-tels/',
    response_model=schemas.SingleEntityResponse[schemas.GettingWhiteTel],
    name="Добавить белый номер телефона",
    description="Добавить новый белый номер телефона",
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
    tags=["Административная панель / Белые номера телефонов"]
)
def create_white_tel(
        data: schemas.CreatingWhiteTel,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
):

    white_tel = crud.white_tel.create(db, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.white_tel.get_white_tel(white_tel)
    )


@router.put(
    '/cp/white-tels/{white_tel_id}/',
    response_model=schemas.SingleEntityResponse[schemas.GettingWhiteTel],
    name="Изменить белый номер телефона",
    description="Изменить белый номер телефона",
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
            'description': 'Белый номер телефона не найдена'
        }
    },
    tags=["Административная панель / Белые номера телефонов"]
)
def edit_white_tel(
        data: schemas.UpdatingWhiteTel,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        white_tel_id: int = Path(..., description="Идентификатор белого номера телефона")
):

    white_tel = crud.white_tel.get_by_id(db, white_tel_id)
    if white_tel is None:
        raise UnfoundEntity(
            message="Белый номер телефона не найден"
        )
    white_tel = crud.white_tel.update(db, db_obj=white_tel, obj_in=data)

    return schemas.SingleEntityResponse(
        data=getters.white_tel.get_white_tel(white_tel)
    )


@router.delete(
    '/cp/white-tels/{white_tel_id}/',
    response_model=schemas.OkResponse,
    name="Удалить белый номер телефона",
    description="Удалить белый номер телефона",
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
            'description': 'Белый номер телефона не найден'
        }
    },
    tags=["Административная панель / Белые номера телефонов"]
)
def delete_white_tel(
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser),
        white_tel_id: int = Path(..., description="Идентификатор белого номера телефона")
):

    white_tel = crud.white_tel.get_by_id(db, white_tel_id)
    if white_tel is None:
        raise UnfoundEntity(
            message="Белый номер телефона не найден"
        )

    crud.white_tel.remove(db=db, id=white_tel_id)

    return schemas.OkResponse()