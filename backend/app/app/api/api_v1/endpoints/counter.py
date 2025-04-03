from typing import Optional

import fastapi
from fastapi import APIRouter, Header, Depends
from sqlalchemy.orm import Session
from user_agents import parse

from app import schemas, crud, getters
from app.api import deps

router = APIRouter()

@router.get(
    "/app/",
    name="Получить клиентское приложение",
    description=
    "Получить клиентское приложение",
    responses={
        400: {
            'model': schemas.OkResponse,
            'description': 'Переданы невалидные данные'
        },
        422: {
            'model': schemas.OkResponse,
            'description': 'Переданные некорректные данные'
        }
    },
    tags=["Мобильное приложение / Счётчики"]
)
def redirect_to_client_app(
        user_agent: Optional[str] = Header(None),
        db: Session = Depends(deps.get_db),
) :
    detected_os = None
    if user_agent is not None:
        ua_string = str(user_agent)
        ua_object = parse(ua_string)

        detected_os = ua_object.os.family
        if detected_os is None or detected_os.lower() == 'other':
            if 'okhttp' in user_agent.lower():
                detected_os = 'Android'
            elif 'cfnetwork' in user_agent.lower():
                detected_os = 'iOS'


    if detected_os is not None and detected_os.lower() == 'android':
        counter = crud.counter.get_or_create(db=db, platform='android')
        counter.value += 1
        db.add(counter)
        db.commit()
        return fastapi.responses.RedirectResponse('market://details?id=ru.axas.portugal',)
    else:
        counter = crud.counter.get_or_create(db=db, platform='ios')
        counter.value += 1
        db.add(counter)
        db.commit()
        return fastapi.responses.RedirectResponse('https://apps.apple.com/us/app/all-portugal/id1667164303',)



@router.get(
    '/cp/counters/',
    tags=['Административная панель / Счётчики'],
    response_model=schemas.ListOfEntityResponse[schemas.GettingCounter],
    name="Получить все счётчики",

)
def get_all(
        db: Session = Depends(deps.get_db)
):
    return schemas.ListOfEntityResponse(
        data=[
            getters.counter.get_counter(counter)
            for counter
            in crud.counter.get_multi(db=db, page=None)[0]
        ]
    )