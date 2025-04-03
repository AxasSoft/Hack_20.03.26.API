import enum
from typing import Optional, List

from app.schemas import GettingUserShortAdminInfo
from pydantic import BaseModel, Field

from . import GettingStoryAttachment, GettingHashtag
from .id_model import IdModel


class Reason(enum.Enum):
    spam = 0
    nudity = 1
    hostility = 2
    violence = 3
    bullying = 4
    forbidden_product = 5
    intellectual_property_rights = 6
    suicide = 7
    eating_disorder = 8
    deceit = 9
    fake = 10


class CreatingUserReport(BaseModel):
    reason: Optional[Reason] = Field(None, title='причина жалобы',description="""Причина жалобы  
    `0` - Спам  
    `1` - Изображения обнаженного тела или действий сексуального характера  
    `2` - Враждебные высказывания или символы Враждебные высказывания или символы  
    `3` - Насилие или опасные организации  
    `4` - Травля или преследования  
    `5` - Продажа незаконных товаров или товаров, подлежащих правовому регулированию  
    `6` - Нарушение прав на интеллектуальную собственность  
    `7` - Самоубийство или нанесение себе увечий  
    `8` - Расстройство пищевого поведения  
    `9` - Мошенничество или обман  
    `10` - Ложная информация  """)
    additional_text: Optional[str] = Field(None, title='текст жалобы')


class UpdatingUserReport(BaseModel):
    is_satisfy: Optional[bool] = Field(None, title='Удовлетворённость')


class GettingUserReport(IdModel, BaseModel):
    created: int = Field(..., title='дата создания заявки')
    subject: GettingUserShortAdminInfo = Field(..., title='Субъект жалобы')
    object: GettingUserShortAdminInfo = Field(..., title='Объект жалобы')
    reason: Optional[Reason] = Field(None, title='причина жалобы',description="""Причина жалобы  
    `0` - Спам  
    `1` - Изображения обнаженного тела или действий сексуального характера  
    `2` - Враждебные высказывания или символы Враждебные высказывания или символы  
    `3` - Насилие или опасные организации  
    `4` - Травля или преследования  
    `5` - Продажа незаконных товаров или товаров, подлежащих правовому регулированию  
    `6` - Нарушение прав на интеллектуальную собственность  
    `7` - Самоубийство или нанесение себе увечий  
    `8` - Расстройство пищевого поведения  
    `9` - Мошенничество или обман  
    `10` - Ложная информация  """)
    additional_text: Optional[str] = Field(None, title='текст жалобы')
    is_satisfy: Optional[bool] = Field(None, title='Удовлетворённость')
