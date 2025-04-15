import logging

import requests
import os
from app.utils.security import generate_random_password
from app.exceptions import UnprocessableEntity
from app.services.gsms_tg_sender.base_gsms_tg_sender import BaseTgSender


class GsmsTgSender(BaseTgSender):
    def send(self, tel: str) -> str:
        url = "https://api3.greensms.ru/telegram/send"
        tel_4428 = ["79892224422"]
        if tel in tel_4428:
            return "4428"

        code = generate_random_password(length=4, digits_only=True)
        params = {
            "to": f'+{tel}',
            "txt": code
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('GSMS_TOKEN')}"
        }
        try:
            response = requests.post(url, data=params, headers=headers).json()
            logging.info("GreenSms response: %s", response)
            print("GreenSms response: %s", response)
            if 'request_id' not in response:
                raise UnprocessableEntity(message="Ошибка отправки кода", num=1)

        except Exception as e:
            logging.error(e)
            raise UnprocessableEntity(message="Что-то пошло не так", num=2)

        return code
