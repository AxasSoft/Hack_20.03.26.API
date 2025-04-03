import csv
import io
from typing import Optional, List, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import not_
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import User
from app.models.black_tel import BlackTel
from app.schemas import Paginator
from app.schemas.black_tel import CreatingBlackTel, UpdatingBlackTel
from app.utils import pagination


class CRUDBlackTel(CRUDBase[BlackTel, CreatingBlackTel, UpdatingBlackTel]):
    def get_multi(
            self, db: Session, *, page: Optional[int] = None
    ) -> Tuple[List[BlackTel], Paginator]:
        query = db.query(self.model).order_by(self.model.tel)

        return pagination.get_page(query, page)

    def create(self, db: Session, *, obj_in: CreatingBlackTel) -> BlackTel:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        for user in db.query(User).filter(User.tel == obj_in.tel, not_(User.in_blacklist)):
            user.in_blacklist = True
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

black_tel = CRUDBlackTel(BlackTel)