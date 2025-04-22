import asyncio
import logging
from typing import List

from emails import Message

from app.core.config import settings

from .base_sender import BaseEmailSender


class SmtpEmailSender(BaseEmailSender):
    def __init__(self, recipients: List[str]=settings.SUPERUSER_EMAIL):
        self.recipients = recipients

    def _send_email(self, recipient, message, smtp_options):
        """Отправляет письмо одному получателю и возвращает (email, response)."""
        response = message.send(
            to=recipient,
            mail_from=settings.SMTP_USER,
            set_mail_from=True,
            smtp=smtp_options,
        )
        logging.info(
            "%s status code: %s\nstatus text: %s",
            recipient,
            response.status_code,
            response.status_text,
        )
        return recipient, response

    def send_email(self, subject: str, body: str) -> List[tuple]:
        """Отправляет письма всем получателям.  -> list[(email, response)]

        response.status_code, response.status_text"""
        message = Message(
            subject=subject,
            html=body,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "tls": settings.SMTP_TLS,
            "user": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
        }
        logging.info("smtp options: %s", smtp_options)
        results = []
        for recipient in self.recipients:
            try:
                result = self._send_email(recipient, message, smtp_options)
                results.append(result)
            except Exception as e:
                logging.error(f"Ошибка отправки для {recipient}: {str(e)}")
                results.append((recipient, None))
        return results


su_email_sender = SmtpEmailSender(recipients=settings.SUPERUSER_EMAIL)
