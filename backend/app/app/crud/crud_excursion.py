from typing import Optional, Union, Dict, Any, Type, List
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import Numeric, text, alias, func, or_, and_, select
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.crud.base import CRUDBase
from app.models import User, ExcursionParticipant, ExcursionImage
from app.models.excursion import Excursion
from app.models.excursion_review import ExcursionReview
from app.schemas.excursion import CreatingExcursion, UpdatingExcursion
from app.exceptions import UnprocessableEntity
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp




class CRUDExcursion(CRUDBase[Excursion, CreatingExcursion, UpdatingExcursion]):

    def __init__(self, model: Type[Excursion]):

        self.s3_bucket_name: Optional[str] = None
        self.s3_client: Optional[BaseClient] = None
        super().__init__(model=model)

    def get_image_by_id(self, db: Session, id: Any):
        return db.query(ExcursionImage).filter(ExcursionImage.id == id).first()

    def add_image(self, db: Session, *, excursion: Excursion, image: UploadFile, num: Optional[int] = None) -> Optional[ExcursionImage]:

        host = self.s3_client._endpoint.host

        bucket_name = self.s3_bucket_name

        url_prefix = host + '/' + bucket_name + '/'

        name = 'excursion/images/' + uuid.uuid4().hex + os.path.splitext(image.filename)[1]

        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=image.file,
            ContentType=image.content_type
        )

        if not (200 <= result.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) < 300):
            return None

        image = ExcursionImage()
        image.excursion = excursion
        image.image = new_url
        image.num = num
        db.add(image)

        db.commit()
        db.refresh(excursion)

        return image

    def delete_image(self, db: Session, *, image: ExcursionImage) -> None:
        db.delete(image)
        db.commit()

    def update_rating(self, db: Session, excursion_id: int):
        excursion = self.get_by_id(db, excursion_id)
        stmt = select(
            func.round(
                func.cast(
                    func.avg(ExcursionReview.rating),
                    Numeric(2, 1)
                ), 1).label("avg_rating"),
                func.count(ExcursionReview.id).label("total_reviews")
        ).filter(ExcursionReview.excursion_id == excursion_id,
                 ExcursionReview.rating.is_not(None),
                 ExcursionReview.rating != 0
                 )
        # rate = db.scalar(stmt)
        result = db.execute(stmt).fetchone()
        print(result)
        print(result.avg_rating)

        excursion.avg_rating = result.avg_rating if result.avg_rating else 0
        excursion.total_reviews = result.total_reviews if result else 0
        db.commit()
        db.commit()


    def get_by_category(self,
                         db: Session,
                         category_id: int,
                         page: Optional[int] = None):
        query = db.query(Excursion).filter(Excursion.category_id == category_id).order_by(Excursion.created.desc())
        return pagination.get_page(query, page)

    # def search(
    #         self,
    #         db: Session,
    #         name: Optional[str] = None,
    #         # price_from: Optional[int]= None,
    #         # price_to: Optional[int]= None,
    #         current_lon: Optional[float]= None,
    #         current_lat: Optional[float]= None,
    #         distance: Optional[int]= None,
    #         page:Optional[int]= None,
    #         is_private: Optional[bool] = None,
    #         statuses: Optional[List[ExcursionStatus]] = None
    # ):
    #     query = db.query(self.model)
    #
    #     if name is not None:
    #         query = query.filter(self.model.name.ilike(f'@{name}%'))
    #
    #     # if price_from is not None:
    #     #     query = query.filter(self.model.price >= price_from)
    #     #
    #     # if price_to is not None:
    #     #     query = query.filter(self.model.price <= price_to)
    #
    #     if statuses is not None and len(statuses) > 0:
    #         query = query.filter(self.model.status.in_(statuses))
    #
    #     if all(x is not None for x in (current_lon, current_lat, distance,)):
    #
    #         sq = db.query(
    #             self.model.id.label('excursion_id'),
    #             func.st_distancespheroid(
    #                 text('''ST_SetSRID(ST_MakePoint(excursion.lat, excursion.lon), 4326)'''),
    #                 text('''ST_SetSRID(ST_MakePoint(:current_lat, :current_lon), 4326)''').bindparams(
    #                     current_lat=current_lat,
    #                     current_lon=current_lon
    #                 ),
    #             ).label('d')
    #         ).subquery()
    #
    #         query = query.join(sq, sq.c.excursion_id == self.model.id,isouter=True).filter(sq.c.d < distance).order_by(sq.c.d)
    #
    #     return pagination.get_page(query,page)


    # def create(
    #         self,
    #         db: Session,
    #         *,
    #         obj_in: Union[CreatingExcursion, Dict[str, Any]]
    # ) -> Excursion:
    #     if isinstance(obj_in, dict):
    #         update_data = obj_in
    #     else:
    #         update_data = obj_in.dict(exclude_unset=True)
    #
    #     participant_ids = update_data.pop('members')
    #     db_obj = self.model(**update_data)
    #     db.add(db_obj)
    #     db.commit()
    #     db.refresh(db_obj)
    #
    #     max_excursion_group_size = db_obj.max_group_size
    #
    #     # if 'max_group_size' in update_data:
    #     #     max_excursion_group_size = update_data['max_group_size']
    #
    #     if max_excursion_group_size is not None and len(participant_ids) > max_excursion_group_size:
    #         raise UnprocessableEntity('Слишком много участников')
    #
    #     for participant_id in participant_ids:
    #         event_member = ExcursionParticipant(user_id=participant_id, excursion=db_obj)
    #         db.add(event_member)
    #
    #     db.commit()
    #     db.refresh(db_obj)
    #
    #     return db_obj


    # def update(
    #     self,
    #     db: Session,
    #     *,
    #     db_obj: Excursion,
    #     obj_in: Union[UpdatingExcursion, Dict[str, Any]]
    # ) -> Excursion:
    #     if isinstance(obj_in, dict):
    #         update_data = obj_in
    #     else:
    #         update_data = obj_in.dict(exclude_unset=True)
    #     if 'started' in update_data:
    #         update_data['started'] = from_unix_timestamp(update_data['started'])
    #     if 'ended' in update_data:
    #         update_data['ended'] = from_unix_timestamp(update_data['ended'])
    #     participant_ids = update_data.pop('members')
    #
    #     for field in dir(db_obj):
    #         if field in update_data:
    #             setattr(db_obj, field, update_data[field])
    #     db.add(db_obj)
    #
    #     max_excursion_group_size = db_obj.max_group_size
    #
    #     if 'max_group_size' in update_data:
    #         max_excursion_group_size = update_data['max_group_size']
    #
    #     if max_excursion_group_size is not None and len(participant_ids) > max_excursion_group_size:
    #         raise UnprocessableEntity('Слишком много участников')
    #
    #     for participant_id in participant_ids:
    #         event_member = ExcursionParticipant(user_id=participant_id, excursion=db_obj)
    #         db.add(event_member)
    #
    #     db.commit()
    #     db.refresh(db_obj)
    #
    #     return db_obj


    # def participant_exist(self, db: Session, user_id: int, excursion_id: int) -> bool:
    #     return db.query(ExcursionParticipant).filter(ExcursionParticipant.user_id == user_id,
    #                                                  ExcursionParticipant.excursion_id == excursion_id).first() is not None
    #
    # def add_participant(self, db: Session, user_id: int, excursion_id: int) -> ExcursionParticipant:
    #     excursion_participant = ExcursionParticipant()
    #     excursion_participant.event_id = excursion_id
    #     excursion_participant.user_id = user_id
    #     db.add(excursion_participant)
    #     db.commit()
    #     db.refresh(excursion_participant)
    #     return excursion_participant
    #
    #
    # def delete_participant(self, db: Session, *, excursion_participant: ExcursionParticipant) -> None:
    #     db.delete(excursion_participant)
    #     db.commit()
    #
    #
    # def get_participant(self, db: Session, excursion_participant_id: int) -> Optional[ExcursionParticipant]:
    #     return db.query(ExcursionParticipant).filter(ExcursionParticipant.id == excursion_participant_id).first()

    # def moderate(self, db: Session, *, event: Event, moderation_body: ModerationBody):
    #     event.status = moderation_body.status
    #     event.moderation_comment = moderation_body.comment
    #     db.add(event)
    #     db.commit()
    #     return event

excursion = CRUDExcursion(Excursion)