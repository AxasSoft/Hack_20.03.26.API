from app.db.base_class import Base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class PromoOrder(Base):
    id = Column(Integer, primary_key=True, index=True)

    cover = Column(String, nullable=True)
    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    link = Column(String, nullable=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=True)
    subcategory_id = Column(Integer, ForeignKey('subcategory.id'), nullable=True)
    info_id = Column(Integer, ForeignKey('info.id'), nullable=True)

    order = relationship("Order", foreign_keys=[order_id], back_populates='promo_order')
    subcategory = relationship("Subcategory", foreign_keys=[subcategory_id], back_populates='promo_order')
    info = relationship("Info", foreign_keys=[info_id], back_populates='promo_order')
