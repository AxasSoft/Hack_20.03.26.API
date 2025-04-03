import enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from .category import GettingCategory
from .id_model import IdModel

# from .user_interest import UserInterestSchema


class Gender(enum.Enum):
    male = 0
    female = 1
    non_answered = 2
    other = 3


class GettingUser(IdModel, BaseModel):
    email: Optional[str] = Field(..., title="Email адрес")
    tel: Optional[str]
    is_active: bool = Field(..., title="Активирован")
    is_superuser: bool = Field(..., title="Суперпользователь")
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    birthtime: Optional[int]
    avatar: Optional[str] = Field(None, title="Аватар пользователя")
    gender: Optional[Gender] = Field(
        None,
        title="Пол пользователя",
        description="0 - Мужской  \n 1 - Женский  \n 2 - предпочитаю не отвечать  \n",
    )
    location: Optional[str]
    rating: float = Field(0)
    created_orders_count: int = Field(0)
    completed_orders_count: int = Field(0)
    my_offers_count: int = Field(0)
    category_id: Optional[int]
    category: Optional[GettingCategory]
    stories_count: int = Field(0, title="Количество постов")
    hugs_count: int = Field(0, title="Количество объятий")
    last_visited: Optional[int] = Field(None, title="Последний раз посещал")
    last_visited_human: Optional[str] = Field(
        None, title="Последний раз посещал (в человеко-понятнов виде)"
    )
    is_online: bool = Field(..., title="В сети")
    i_block: bool = Field(False, title="Вы заблокировали этого пользователя")
    block_me: bool = Field(False, title="Этот пользователь заблокировал вас")
    tg: Optional[str]
    is_servicer: Optional[bool] = Field(False)
    in_blacklist: bool = Field(False)
    in_whitelist: bool = Field(False)
    is_business: bool = Field(False)
    is_compatriot: bool = Field(False)
    show_tel: bool = Field(True)
    region: Optional[str] = Field(None)
    site: Optional[str] = Field(None)
    count_feedback_order: Optional[int]
    experience: Optional[str] = Field(None)
    company_info: Optional[str] = Field(None)
    in_subscriptions: Optional[bool] = Field(None)
    lat: Optional[float] = Field(None)
    lon: Optional[float] = Field(None)
    country: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    subscriptions_count: int = Field(0)
    subscribers_count: int = Field(0)
    profile_cover: Optional[str]
    is_dating_profile: Optional[bool] = Field(False)
    is_editor: bool = Field(False)
    is_support: Optional[bool] = Field(False)


class UpdatingUser(BaseModel):
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    birthtime: Optional[int]
    category_id: Optional[int]
    gender: Optional[Gender] = Field(
        None,
        title="Пол пользователя",
        description="""0 - Мужской  
        1 - Женский""",
    )
    location: Optional[str]
    is_servicer: Optional[bool]
    email: Optional[str] = Field(None, title="Email адрес")
    tg: Optional[str]
    is_business: Optional[bool]
    show_tel: Optional[bool]
    region: Optional[str] = Field(None)
    site: Optional[str] = None
    experience: Optional[str] = None
    company_info: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    country: Optional[str] = None
    is_compatriot: Optional[bool] = Field(False)
    status: Optional[str] = None
    is_dating_profile: Optional[bool] = Field(False)


class UpdatingUserByAdmin(UpdatingUser):
    is_active: Optional[bool] = Field(None, title="Активирован")
    tel: Optional[str]
    in_blacklist: Optional[bool]
    in_whitelist: Optional[bool]
    is_editor: Optional[bool]
    is_support: Optional[bool]
    is_superuser: Optional[bool]


class EmailBody(BaseModel):
    email: str = Field(..., title="Email адрес")


class TelBody(BaseModel):
    tel: str


class PasswordBody(BaseModel):
    password: str = Field(..., title="Пароль")


class ExistsBody(BaseModel):
    exists: bool = Field(
        ..., title="Объект с указазанным критерием уже существует в системе"
    )


class LoginForm(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class GettingUserShortInfo(IdModel, BaseModel):
    email: Optional[str] = Field(..., title="Email адрес")
    tel: Optional[str]
    is_active: bool = Field(..., title="Активирован")
    is_superuser: bool = Field(..., title="Суперпользователь")
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    birthtime: Optional[int]
    avatar: Optional[str] = Field(None, title="Аватар пользователя")
    gender: Optional[Gender] = Field(
        None, title="Пол пользователя", description="0 - Мужской  \n 1 - Женский"
    )
    location: Optional[str]
    rating: float = Field(0)
    count_feedback_order: Optional[int]
    last_visited: Optional[int] = Field(None, title="Последний раз посещал")
    last_visited_human: Optional[str] = Field(
        None, title="Последний раз посещал (в человеко-понятнов виде)"
    )
    is_online: bool = Field(..., title="В сети")
    category_id: Optional[int]
    category: Optional[GettingCategory]
    tg: Optional[str]
    is_servicer: Optional[bool] = Field(False)
    in_blacklist: bool = Field(False)
    in_whitelist: bool = Field(False)
    is_business: bool = Field(False)
    is_compatriot: Optional[bool] = Field(None)
    show_tel: bool = Field(True)
    region: Optional[str] = Field(None)
    site: Optional[str] = Field(None)
    experience: Optional[str] = Field(None)
    company_info: Optional[str] = Field(None)
    in_subscriptions: Optional[bool] = Field(None)
    lat: Optional[float] = Field(None)
    lon: Optional[float] = Field(None)
    country: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    subscriptions_count: int = Field(0)
    subscribers_count: int = Field(0)
    profile_cover: Optional[str]
    is_dating_profile: Optional[bool] = Field(False)


class Device(IdModel, BaseModel):
    user_agent: Optional[str]
    ip_address: Optional[str]
    x_real_ip: Optional[str]
    accept_language: Optional[str]
    created: Optional[int]
    detected_os: Optional[str]


class AdminInfo(BaseModel):
    device: Optional[Device]
    created: Optional[int]
    deleted: Optional[int]


class GettingUserShortAdminInfo(GettingUserShortInfo, AdminInfo):
    is_superuser: bool = Field(..., title="Суперпользователь")


class GettingUserWithAdminInfo(GettingUser, AdminInfo):
    pass


class BlockBody(BaseModel):
    block: bool = Field(..., title="Заблокировать пользователя")


class EmailAndPassword(BaseModel):
    email: str = Field(..., title="Email")
    password: str = Field(..., title="Пароль")


class CreatingPushNotification(BaseModel):
    title: Optional[str]
    body: Optional[str]
    link: Optional[str]


class GettingPushNotification(BaseModel):
    id: int
    title: Optional[str]
    body: Optional[str]
    created: Optional[int]
    link: Optional[str]


class ByCategorySchema(BaseModel):
    category_id: int
    count: int


class GettingStat(BaseModel):
    user_current_count: int
    user_total_count: int
    compatriot_total_count: int
    compatriot_current_count: int
    not_compatriot_total_count: int
    not_compatriot_current_count: int
    order_current_count: int
    order_completed_count: int
    order_total_count: int
    current_info_by_category: List[ByCategorySchema]
    total_info_by_category: List[ByCategorySchema]
    white_tel_count: int
    black_tel_count: int
    story_current_count: int
    story_total_count: int


class SubscribeBody(BaseModel):
    subscribe: bool = Field(
        ...,
        title="Подписаться",
        description="Флаг, означающий подписку(`true`) или отписку (`false`)",
    )


class CreatingUser(BaseModel):
    email: Optional[str] = Field(..., title="Email адрес")
    tel: Optional[str]
    is_active: bool = Field(..., title="Активирован")
    is_superuser: bool = Field(..., title="Суперпользователь")
    first_name: Optional[str]
    patronymic: Optional[str]
    last_name: Optional[str]
    birthtime: Optional[int]
    gender: Optional[Gender] = Field(
        None,
        title="Пол пользователя",
        description="0 - Мужской  \n 1 - Женский  \n 2 - предпочитаю не отвечать  \n",
    )
    location: Optional[str]
    category_id: Optional[int]
    tg: Optional[str]
    is_servicer: Optional[bool] = Field(False)
    is_business: bool = Field(False)
    show_tel: bool = Field(True)
    region: Optional[str] = Field(None)
    site: Optional[str] = Field(None)
    experience: Optional[str] = Field(None)
    company_info: Optional[str] = Field(None)
    lat: Optional[float] = Field(None)
    lon: Optional[float] = Field(None)
    # compatriot: Optional[bool] = Field(False)
    status: Optional[str] = Field(None)
    is_dating_profile: Optional[bool] = Field(False)
    is_editor: Optional[bool]
    is_support: Optional[bool]
    interests: Optional[List[int]]
