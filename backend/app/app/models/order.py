import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM

from app.db.base_class import Base
from app.enums.mod_status import ModStatus


class Stage(enum.Enum):
    created = 0 # Заказ создан. Выбираем отклики
    selected = 1 # Выбрали отклик-победитель
    finished = 2 # Работа с откликом завершена. Ожидаем подтверждения
    confirmed = 3 # Работа с откликом подтверждена
    rejected = 4 # Заказ отклонён


class Order(Base):
    id = Column(Integer, primary_key=True, index=True)

    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    title = Column(String, nullable=True)
    body = Column(String, nullable=True)
    deadline = Column(DateTime, nullable=True)
    profit = Column(Integer, nullable=True)
    stage = Column(Enum(Stage), nullable=False, default=Stage.created)
    address = Column(String, nullable=True, default=None)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    type = Column(String, nullable=True, default=None)
    is_block = Column(Boolean, nullable=True, default=False)
    block_comment = Column(String, nullable=True)
    is_auto_recreate = Column(Boolean, nullable=False, server_default='false')
    status = Column(ENUM(ModStatus), nullable=False, server_default=ModStatus.created.name)
    moderation_comment = Column(String, nullable=True)
    views_counter: int = Column(Integer(), index=True, default=0, server_default='0')

    is_stopping = Column(Boolean(), default=False, server_default='false')

    subcategory_id = Column(Integer, ForeignKey('subcategory.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    subcategory = relationship('Subcategory', back_populates='orders')
    user = relationship('User', back_populates='orders')

    offers = relationship('Offer', back_populates='order', passive_deletes=True, cascade="all, delete-orphan")
    images = relationship('OrderImage', back_populates='order', passive_deletes=True, cascade="all, delete-orphan", order_by="OrderImage.num")
    favorite_orders = relationship(
        'FavoriteOrder', back_populates='order', passive_deletes=True, cascade="all, delete-orphan")
    

    promo_order = relationship('PromoOrder', back_populates='order')

    feedback_order = relationship('FeedbackOrder', back_populates='order', cascade="all, delete-orphan")

    views_order = relationship('OrderView', back_populates='order', foreign_keys='OrderView.order_id')
