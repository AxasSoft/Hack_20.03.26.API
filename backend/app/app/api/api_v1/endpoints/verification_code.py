import datetime
import json
from typing import Optional, List
import logging
import asyncio

from fastapi import APIRouter, Depends, Query, UploadFile, WebSocket, Header
from fastapi.params import Path, File, Form
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from app import crud, models, schemas, getters
from app.api import deps

router = APIRouter()

@router.post(
    '/verification-codes/',
    response_model=schemas.response.SingleEntityResponse[schemas.verification_code.GettingVerificationCode],
    name="Оправить код подтверждения",
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
    tags=["Вход"]
)
async def send_code(
        data: schemas.verification_code.CreatingVerificationCode,
        db: Session = Depends(deps.get_db),
):
    code = crud.crud_verification_code.verification_code.create(db=db, obj_in=data)
    return schemas.response.SingleEntityResponse(data=getters.verification_code.get_verification_code(code))
