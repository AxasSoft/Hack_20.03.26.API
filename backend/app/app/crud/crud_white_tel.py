import csv
import io
from typing import Optional, List, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import not_
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import User
from app.models.white_tel import WhiteTel
from app.schemas import Paginator
from app.schemas.white_tel import CreatingWhiteTel, UpdatingWhiteTel
from app.utils import pagination


class CRUDWhiteTel(CRUDBase[WhiteTel, CreatingWhiteTel, UpdatingWhiteTel]):
    def get_multi(
            self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[WhiteTel], Paginator]:
        query = db.query(self.model).order_by(self.model.tel)

        return pagination.get_page(query, page)

    def create(self, db: Session, *, obj_in: CreatingWhiteTel) -> WhiteTel:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        for user in db.query(User).filter(User.tel == obj_in.tel, not_(User.in_whitelist)):
            user.in_whitelist = True
            db.add(user)
        db.commit()


        return db_obj

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

white_tel = CRUDWhiteTel(WhiteTel)