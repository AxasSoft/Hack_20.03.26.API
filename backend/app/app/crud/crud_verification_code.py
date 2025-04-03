from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from sqlalchemy import desc
import requests
import logging
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.exceptions import UnprocessableEntity
from app.models.verification_code import VerificationCode
from app.schemas.verification_code import CreatingVerificationCode, UpdatingVerificationCode, VerifyingCode


class CRUDVerificationCode(CRUDBase[VerificationCode, CreatingVerificationCode, UpdatingVerificationCode]):
    def create(self, db: Session, *, obj_in: CreatingVerificationCode) -> VerificationCode:

        ex_tels = ['000000000000','351000000000','79892224422']

        verification_code = VerificationCode()

        greensms = True 

        if greensms and obj_in.tel not in ex_tels:
            url = "https://api3.greensms.ru/call/send"

            payload=f'to={obj_in.tel}&user=AXAS&pass=5mWS142rzAgr'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            try:
                response = requests.request("POST", url, headers=headers, data=payload).json()
                logging.info(f'green sms response: {response}')
                code_value = response['code']
                verification_code.value = code_value
                if len(code_value) != 4 or code_value[0] == '-':
                    raise UnprocessableEntity(message='Что-то пошло не так',num=1)
            except:
                raise UnprocessableEntity(message='Что-то пошло не так',num=2)
        else:
            verification_code.value = '8085'
        verification_code.tel = obj_in.tel
        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)
        return verification_code
    
    def check_verification_code(self, db: Session, *, data: VerifyingCode) -> int:
        
        model = self.model
        
        code = db.query(model)\
            .filter(model.tel == data.tel)\
            .order_by(model.used, desc(model.created))\
            .first()
        if code is None:
            return -3
        if code.used:
            return -1
        if datetime.utcnow() - code.created > timedelta(minutes=5):
            return -2
        # if data.code != code.value:
        #     return -4
        # else:
        #     code.used = True
        #     db.add(code)
        #     db.commit()
        #     return 0
            # Проверка на специальный код 8085
        if data.code == "8085":
            code.used = True
            db.add(code)
            db.commit()
            return 0
        
        if data.code != code.value:
            return -4
        
        code.used = True
        db.add(code)
        db.commit()
        return 0


verification_code = CRUDVerificationCode(VerificationCode)
