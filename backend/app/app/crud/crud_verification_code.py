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
from app.services.gsms_tg_sender.base_gsms_tg_sender import BaseTgSender


class CRUDVerificationCode(CRUDBase[VerificationCode, CreatingVerificationCode, UpdatingVerificationCode]):
    def create(self, db: Session, gsms_tg_sender: BaseTgSender, *,
               obj_in: CreatingVerificationCode) -> VerificationCode:
        code = gsms_tg_sender.send(tel=obj_in.tel)
        verification_code = VerificationCode(tel=obj_in.tel, value=code)
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
        # if data.code == "8085":
        #     code.used = True
        #     db.add(code)
        #     db.commit()
        #     return 0
        
        if data.code != code.value:
            return -4
        
        code.used = True
        db.add(code)
        db.commit()
        return 0


verification_code = CRUDVerificationCode(VerificationCode)
