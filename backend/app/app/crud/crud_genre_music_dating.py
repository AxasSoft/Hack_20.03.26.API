from typing import Union, Dict, Any, Optional, Tuple, List

from app.crud.base import CRUDBase
from app.models import GenreMusic, User
from app.schemas import CreatingGenreMusic, UpdatingGenreMusic, GenreMusicSubGenreMusic, SubGenreMusic
from app.schemas.response import Paginator
from app.utils import pagination
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

class CRUDGenreMusic(CRUDBase[GenreMusic, CreatingGenreMusic, UpdatingGenreMusic]):
        
    def update(
            self,
            db: Session,
            *,
            db_obj: GenreMusic,
            obj_in: Union[UpdatingGenreMusic, Dict[str, Any]],
            **kwargs
    ) -> GenreMusic:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        return super().update(db,db_obj=db_obj,obj_in=update_data)
    


    def get_genremusic(self, db: Session, page: int = None, page_size: int = None):
        query = db.query(GenreMusic).filter(GenreMusic.parent_genre_music_id == None)
        
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        
        genre_music = query.all()
        total = query.count()
        
        return genre_music, total


    def get_all_genremusic_subgenremusic(self, db: Session) -> List[GenreMusicSubGenreMusic]:
        genremusic = db.query(GenreMusic).filter(GenreMusic.parent_genre_music_id == None).options(joinedload(GenreMusic.sub_genre_music)).all()
        
        result = []

        for genremusic in genremusic:
        
            sub_genre_music = []  
            if genremusic.sub_genre_music is not None:
                for sub_music in genremusic.sub_genre_music:
                    sub_genre_music.append(SubGenreMusic(
                    sub_genre_music_id=sub_music.id,
                    sub_genre_music_name=sub_music.genre_music_name
                ))
            else:
                sub_genre_music = []
            genre_music_sub_genre_music = GenreMusicSubGenreMusic(
                genre_music_id=genremusic.id,
                genre_music_name=genremusic.genre_music_name,
                sub_genre_music=sub_genre_music
            )
            result.append(genre_music_sub_genre_music)
            
        return result
    


genre_music = CRUDGenreMusic(GenreMusic)