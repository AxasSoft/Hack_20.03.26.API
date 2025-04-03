import csv
import datetime
import io
import logging
from typing import Optional, Tuple, List, Union, Dict, Any, Type

from sqlalchemy import or_, desc, and_, asc
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.base import CRUDBase
from app.enums.mod_status import ModStatus
from app.models import Offer, Category, Subcategory, FavoriteOrder
from app.models.order import Order, Stage
from app.models.order_image import OrderImage
from app.models.order_view import OrderView
from app.models.user import User
from app.schemas import Paginator
from app.schemas.order import CreatingOrder, UpdatingOrder, ModerationBody
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp
from botocore.client import BaseClient
from fastapi import UploadFile
from typing import Optional, Union, Dict, Any
import uuid
import os


class CrudOrder(CRUDBase[Order, CreatingOrder, UpdatingOrder]):

    def __init__(self, model: Type[Order]):

        self.s3_bucket_name: Optional[str] = deps.get_bucket_name()
        self.s3_client: Optional[BaseClient] = deps.get_s3_client()
        super().__init__(model=model)
    
    def create_by_user(self, db: Session, *, obj_in: CreatingOrder, user: User) -> Order:
        order = Order()

        data = obj_in.dict(exclude_unset=True)

        order.user = user
        order.title = data.get('title', None)
        order.body = data.get('body', None)
        order.deadline = from_unix_timestamp(data.get('deadline', None))
        order.profit = data.get('profit', None)
        order.subcategory_id = data.get('subcategory_id', None)
        order.type = data.get('type', None)
        order.address = data.get('address', None)
        order.is_auto_recreate = bool(data.get('is_auto_recreate', False))
        order.lat = data.get('lat', None)
        order.lon = data.get('lon', None)
        user.created_orders_count += 1
        user.rating += 5

        db.add(user)
        db.add(order)
        db.commit()

        return order

    def update(
        self,
        db: Session,
        *,
        db_obj: Order,
        obj_in: Union[UpdatingOrder, Dict[str, Any]]
    ) -> Order:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if 'deadline' in update_data:
            update_data['deadline'] = from_unix_timestamp(update_data['deadline'])


        for field in dir(db_obj):
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


    def search(
        self,
        db: Session,
        *,
        page: Optional[int] = None,
        stages: Optional[List[Stage]] = None,
        user: Optional[User] = None,
        is_block: Optional[bool] = None,
        is_winner: Optional[bool] = None,
        current_user: Optional[User] = None,
        address: Optional[str] = None,
        type: Optional[str] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        is_favorite: Optional[bool] = None,
        statuses: Optional[List[ModStatus]] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        sort_by: Optional[str] = None,
        is_stopping: Optional[bool] = None
    ) -> Tuple[List[Order], Paginator]:

        query = db.query(self.model)

        if stages is not None:
            query = query.filter(Order.stage.in_(stages))
        if user is not None and is_winner is None:
            query = query.filter(Order.user == user)

        if address is not None:
            query = query.filter(Order.address.ilike(f'%{address}%'))

        if type is not None:
            query = query.filter(Order.type.ilike(type))

        if is_block == True:
            query = query.filter(Order.is_block == True)
        if is_block == False:
            query = query.filter(or_(Order.is_block == None, Order.is_block == False))

        if is_favorite is not None:
            query = query.join(
            FavoriteOrder,
            and_(
                FavoriteOrder.order_id == Order.id,
                FavoriteOrder.user_id == current_user.id
            ),
            isouter=True
        ).filter((FavoriteOrder.id != None) == is_favorite)


        if category_id is not None:
            query = query.join(Subcategory,Order.subcategory_id == Subcategory.id, isouter=True).filter(Subcategory.category_id == category_id)
        if subcategory_id is not None:
            query = query.filter(Order.subcategory_id == subcategory_id)

        if is_winner is not None and current_user is not None:
            query = query.join(Offer, and_(Offer.order_id == Order.id, Offer.user == current_user, Offer.is_winner != None, Offer.is_winner), isouter=True,)
            if is_winner:
                query = query.filter(Offer.id != None)
            else:
                query = query.filter(Offer.id == None)
        
        if statuses is not None and len(statuses) > 0:   
            query = query.filter(Order.status.in_(statuses))

        if min_price is not None:
            query = query.filter(Order.profit >= min_price)
        if max_price is not None:
            query = query.filter(Order.profit <= max_price)

        if sort_by == "date_asc":
            query = query.order_by(asc(Order.created))
        if sort_by == "date_desc":
            query = query.order_by(desc(Order.created))
        if sort_by == "price_asc":
            query = query.order_by(asc(Order.profit))
        if sort_by == "price_desc":
            query = query.order_by(desc(Order.profit))

        if is_stopping is False:
             query = query.filter(Order.is_stopping == False)
        if is_stopping is True:
             query = query.filter(Order.is_stopping == True)

        query = query.order_by(desc(self.model.created))

        return pagination.get_page(query, page)

    def change_stage(self, db: Session, order: Order, stage: Stage):

        order.stage = stage
        db.add(order)

        if stage == Stage.finished:
            offer = db.query(Offer).filter(Offer.order_id == order.id, Offer.is_winner).first()

            if offer is not None:
                owner = offer.user
                owner.completed_orders_count += 1
                db.add(owner)
        if stage == Stage.confirmed:
            order.confirmed_at = datetime.datetime.utcnow()

        db.commit()

        return order

    def change_block(self, db: Session, order: Order, is_block: bool, comment: Optional[str]):
        order.is_block = is_block
        order.block_comment = comment
        db.add(order)
        db.commit()

        return order


    def remove(self, db: Session, *, id: int):
        order = db.query(Order).get(id)

        for offer in order.offers:
            db.delete(offer)
        db.delete(order)
        db.commit()


    def export(self, db: Session):

        writer_file =  io.StringIO()

        outcsv = csv.writer(writer_file)

        cursor = db \
            .execute(str(db.query(self.model).order_by(self.model.id).statement.compile(dialect=postgresql.dialect()))) \
            .cursor

        # dump column titles (optional)
        outcsv.writerow(x[0] for x in cursor.description)
        # dump rows
        outcsv.writerows(cursor.fetchall())



        return writer_file.getvalue().encode()


    def get_image_by_id(self, db: Session, id: Any):
        return db.query(OrderImage).filter(OrderImage.id == id).first()

    def add_image(self, db: Session, *, order: Order, image: UploadFile, num: Optional[int] = None) -> Optional[OrderImage]:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'order/images/' + uuid.uuid4().hex + os.path.splitext(image.filename)[1]

        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=image.file,
            ContentType=image.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        image = OrderImage()
        image.order = order
        image.image = new_url
        image.num = num
        db.add(image)

        db.commit()

        return image

    def delete_image(self, db: Session, *, image: OrderImage) -> None:
        db.delete(image)
        db.commit()

    def change_is_favorite(self, db: Session, *, user: User, order: Order, is_favorite: bool):
        favorite_order = db.query(FavoriteOrder).filter(
            FavoriteOrder.order == order, FavoriteOrder.user == user).first()
        if is_favorite and favorite_order is None:
            favorite_order = FavoriteOrder()
            favorite_order.order = order
            favorite_order.user = user
            db.add(favorite_order)
            db.commit()
        if not is_favorite and favorite_order is not None:
            db.delete(favorite_order)
            db.commit()

    def moderate(self, db: Session, *, order: Order, moderation_body: ModerationBody):
        order.status = moderation_body.status
        order.moderation_comment = moderation_body.comment
        db.add(order)
        db.commit()
        return order
    
    def make_view(self, db: Session, order_id: int, user_id: int) -> Optional[OrderView]:
        order = db.get(Order, order_id)
        # view = (await db.execute(select(PostView).filter_by(**{'post_id': post_id, 'user_id': user_id}))).scalars().first()
        # view = db.query(OrderView).filter(**{'order_id': order_id, 'user_id': user_id}).first()
        if order:
            view = db.query(OrderView).filter(and_(
                OrderView.order_id==order_id,
                OrderView.user_id==user_id
            )).first()
            
            if not view:
                order.views_counter += 1
                db.add(order)
                view_obj = OrderView()
                view_obj.order_id = order_id
                view_obj.user_id = user_id
                db.add(view_obj)
                db.commit()
                db.refresh(order)
                return view_obj
        else:
            return
    


order = CrudOrder(Order)
