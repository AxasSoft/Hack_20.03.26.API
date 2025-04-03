from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.counter import Counter
from app.schemas.counter import CreatingCounter, UpdatingCounter


class CRUDCounter(CRUDBase[Counter, CreatingCounter, UpdatingCounter]):
    def get_or_create(self, db: Session, platform: str) -> Counter:
        counter =  db.query(self.model).filter(self.model.platform == platform).first()
        if counter:
            return counter
        else:
            counter = Counter()
            counter.platform = platform
            counter.value = 0
            db.add(counter)
            db.commit()
            db.refresh(counter)
            return counter

counter = CRUDCounter(Counter)