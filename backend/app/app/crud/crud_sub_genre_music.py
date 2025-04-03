from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models import GenreMusic , User, ProfileGenreMusic
# from app.schemas import CreatingInterest, UpdatingInterest
from app.schemas.sub_genre_music import CreatingSubGenreMusic, UpdatingSubGenreMusic, GettingSubGenreMusic
from app.schemas.user_interest import UserInterestSchema, SubInterestSchema, InterestSchema
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


class CRUDSubInterest(CRUDBase[GenreMusic, CreatingSubGenreMusic, UpdatingSubGenreMusic]):
        
    def update(
            self,
            db: Session,
            *,
            db_obj: GenreMusic,
            obj_in: Union[UpdatingSubGenreMusic, Dict[str, Any]],
            **kwargs
    ) -> GenreMusic:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db,db_obj=db_obj,obj_in=update_data)

    def create_sub_genre_music(self, db: Session, obj_in: CreatingSubGenreMusic):
        db_obj = GenreMusic(
            genre_music_name=obj_in.genre_music_name,
            parent_genre_music_id=obj_in.parent_genre_music_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    

    def get_sub_genre_music(self,
            db: Session,
            page: int = None, 
            page_size: int = None):

        query = db.query(GenreMusic).filter(GenreMusic.parent_genre_music_id != None)
        
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        
        sub_genre_music = query.all()
        total = query.count()
        
        return sub_genre_music, total
    

    def get_sub_genre_music_current_user(
            self,
            db: Session,
            user: User
        ) -> GettingSubGenreMusic:
        query = db.query(ProfileGenreMusic).filter(ProfileGenreMusic.dating_profile_id == user.dating_profile.id).all()
        sub_genre_music = []
        for profile_genre_music in query:
            genre_music = profile_genre_music.genre_music
            sub_genre_music.append(genre_music)        
        return sub_genre_music


sub_genre_music = CRUDSubInterest(GenreMusic)