from app.services.gsms_tg_sender.base_gsms_tg_sender import BaseTgSender
from app.utils.security import generate_random_password


class FakeTgSender(BaseTgSender):
    pass
