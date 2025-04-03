import os
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union
from sqlalchemy.sql import func
from app import crud
from app.schemas.user import Gender
from app.enums.relationship_type_dating import RelationshipType
from app.api import deps
from datetime import datetime, timedelta
from sqlalchemy import and_, exists, between, select, extract, or_, null
from app.crud.base import CRUDBase
from app.exceptions import UnfoundEntity
from app.models import (
    DatingProfile,
    Facts,
    GenreMusic,
    Interests,
    ProfileAvatar,
    ProfileFacts,
    ProfileGenreMusic,
    ProfileInterests,
    ProfileLike,
    User,
    RatingWeights
)
from app.schemas.dating_profile import (
    CreatingDatingProfile,
    GettingDatingProfile,
    UpdatingDatingProfile,
    LikeDisLikeDatingProfile
)
from app.schemas.response import Paginator
from app.schemas.sub_facts import AddUserProfilSubFacts
from app.schemas.sub_genre_music import AddUserProfilSubGenreMusic
from app.schemas.sub_interest import AddUserProfilSubInterest
from app.utils import pagination
from botocore.client import BaseClient
from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload, aliased

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from collections import Counter
import random
from math import log10

import logging


class CRUDDatingProfile(
    CRUDBase[DatingProfile, CreatingDatingProfile, UpdatingDatingProfile]
):
    T = TypeVar("T")

    def __init__(self, model: Type[DatingProfile]):
        self.s3_bucket_name: Optional[str] = deps.get_bucket_name()
        self.s3_client: Optional[BaseClient] = deps.get_s3_client()
        super().__init__(model=model)


    def _flat(self, list_of_lists):
        return [item for sublist in list_of_lists for item in sublist]

    def _dict_union(self, *dicts):
        return {k: sum(d.get(k, 0) for d in dicts) for k in set(self._flat([d.keys() for d in dicts]))}

    def _tf(self, doc):
        length = len(doc)
        return {word: 1 / length for word in doc}

    def _tf_all(self, docs):
        return self._dict_union(*[self._tf(doc) for doc in docs])

    def _idf(self, docs):
        total = len(docs)
        return {item: log10(1 + total / len([doc for doc in docs if item in doc])) for item in self._flat(docs)}

    def _tf_idf(self, docs):
        tf_scores = self._tf_all(docs)
        idf_scores = self._idf(docs)
        return {k: tf_scores[k] * idf_scores[k] for k in tf_scores.keys()}

    def _rates_analyze(self, profile_id: int, save: bool, display: bool, db: Session):
        print(profile_id)
        print(f"display: {'yes' if display else 'no'}")
        print(f"save: {'yes' if save else 'no'}")

        rate_weight = {
            0: 1.0,  # Высокая оценка
            1: -1.0, # Низкая оценка
            2: 0.3,  # Средняя оценка
            3: 0.6   # Оценка среднего уровня
        }

        category_weight = {
            'interests': 1.0,
            'genre_music': 0.5,
            'facts': 0.7,
            'education': 0.8,
            'work': 0.8,
            'films': 0.5,
            'book': 0.7,
            'about': 0.9,
        }
        
        stmt = select(
            ProfileLike.liker_estimate_type,
            ProfileInterests.interest_id,
            ProfileGenreMusic.sub_genre_music_id,
            ProfileFacts.subfacts_id,
            DatingProfile.education,
            DatingProfile.work,
            DatingProfile.films,
            DatingProfile.book,
            DatingProfile.about,
        ).join(ProfileLike, and_(
            ProfileLike.liked_dating_profile_id == DatingProfile.id,
            ProfileLike.liker_dating_profile_id == profile_id
        )) \
        .join(ProfileInterests, DatingProfile.id == ProfileInterests.dating_profile_id) \
        .join(ProfileGenreMusic, DatingProfile.id == ProfileGenreMusic.dating_profile_id) \
        .join(ProfileFacts, DatingProfile.id == ProfileFacts.dating_profile_id) \
        .where(ProfileLike.liker_dating_profile_id == profile_id)

        result = db.execute(stmt).fetchall()

        if not result:
            logging.info('Profile info null')
            return None

        interest_names = db.execute(select(Interests.id, Interests.interest_name)).fetchall()
        genre_music_names = db.execute(select(GenreMusic.id, GenreMusic.genre_music_name)).fetchall()
        facts_names = db.execute(select(Facts.id, Facts.facts_name)).fetchall()

        interest_name_dict = {id: name for id, name in interest_names}
        genre_music_name_dict = {id: name for id, name in genre_music_names}
        facts_name_dict = {id: name for id, name in facts_names}

        interests = defaultdict(set)
        genre_music = defaultdict(set)
        facts = defaultdict(set)
        education = defaultdict(set)
        work = defaultdict(set)
        films=defaultdict(set)
        book=defaultdict(set)
        about=defaultdict(set)

        for row in result:
            profile_type = row[0]
            
            if row[1]:
                interests[profile_type].add(interest_name_dict.get(row[1], "Unknown Interest"))
            
            if row[2]:
                genre_music[profile_type].add(genre_music_name_dict.get(row[2], "Unknown Genre"))
            
            if row[3]:
                facts[profile_type].add(facts_name_dict.get(row[3], "Unknown Fact"))
            
            if row[4]:
                education[profile_type].add(row[4])
            
            if row[5]:
                work[profile_type].add(row[5])
            
            if row[6]:
                films[profile_type].add(row[6])
            
            if row[7]:
                book[profile_type].add(row[6])

            if row[8]:
                about[profile_type].add(row[6])


        interests = {k: list(v) for k, v in interests.items()}
        genre_music = {k: list(v) for k, v in genre_music.items()}
        facts = {k: list(v) for k, v in facts.items()}
        education = {k: list(v) for k, v in education.items()}
        work = {k: list(v) for k, v in work.items()}
        films = {k: list(v) for k, v in films.items()}
        book = {k: list(v) for k, v in book.items()}
        about = {k: list(v) for k, v in about.items()}


        if display:
            logging.info('-=-=-=-')
            logging.info(interests)
            logging.info(genre_music)
            logging.info(facts)
            logging.info(education)
            logging.info(work)
            logging.info(films)
            logging.info(book)
            logging.info(about)

        interests_relevance = {}
        genre_music_relevance = {}
        facts_relevance = {}
        education_relevance = {}
        work_relevance = {}
        films_relevance = {}
        book_relevance = {}
        about_relevance = {}

        for rate_type, interest_lists in interests.items():
            for interest, weight in self._tf_idf(interest_lists).items():
                if interest in interests_relevance:
                    interests_relevance[interest] += weight * rate_weight[rate_type] * category_weight['interests']
                else:
                    interests_relevance[interest] = weight * rate_weight[rate_type] * category_weight['interests']

        if display:
            logging.info(interests_relevance)
            logging.info()

        for rate_type, genre_music_lists in genre_music.items():
            for genre, weight in self._tf_idf(genre_music_lists).items():
                if genre in genre_music_relevance:
                    genre_music_relevance[genre] += weight * rate_weight[rate_type] * category_weight['genre_music']
                else:
                    genre_music_relevance[genre] = weight * rate_weight[rate_type] * category_weight['genre_music']

        if display:
            logging.info(genre_music_relevance)
            logging.info()

        for rate_type, facts_lists in facts.items():
            for fact, weight in self._tf_idf(facts_lists).items():
                if fact in facts_relevance:
                    facts_relevance[fact] += weight * rate_weight[rate_type] * category_weight['facts']
                else:
                    facts_relevance[fact] = weight * rate_weight[rate_type] * category_weight['facts']

        if display:
            logging.info(facts_relevance)
            logging.info()

        for rate_type, education_lists in education.items():
            for edu, weight in self._tf_idf(education_lists).items():
                if edu in education_relevance:
                    education_relevance[edu] += weight * rate_weight[rate_type] * category_weight['education']
                else:
                    education_relevance[edu] = weight * rate_weight[rate_type] * category_weight['education']

        if display:
            logging.info(education_relevance)
            logging.info()

        for rate_type, work_lists in work.items():
            for job, weight in self._tf_idf(work_lists).items():
                if job in work_relevance:
                    work_relevance[job] += weight * rate_weight[rate_type] * category_weight['work']
                else:
                    work_relevance[job] = weight * rate_weight[rate_type] * category_weight['work']

        if display:
            logging.info(work_relevance)
            logging.info()

        for rate_type, films_lists in films.items():
            for job, weight in self._tf_idf(films_lists).items():
                if job in films_relevance:
                    films_relevance[job] += weight * rate_weight[rate_type] * category_weight['films']
                else:
                    films_relevance[job] = weight * rate_weight[rate_type] * category_weight['films']

        if display:
            logging.info(films_relevance)
            logging.info()

        for rate_type, book_lists in book.items():
            for job, weight in self._tf_idf(book_lists).items():
                if job in book_relevance:
                    book_relevance[job] += weight * rate_weight[rate_type] * category_weight['book']
                else:
                    book_relevance[job] = weight * rate_weight[rate_type] * category_weight['book']

        if display:
            logging.info(book_relevance)
            logging.info()

        for rate_type, about_lists in about.items():
            for job, weight in self._tf_idf(about_lists).items():
                if job in about_relevance:
                    about_relevance[job] += weight * rate_weight[rate_type] * category_weight['about']
                else:
                    about_relevance[job] = weight * rate_weight[rate_type] * category_weight['about']

        if display:
            logging.info(about_relevance)
            logging.info()

        if save:
            db.query(RatingWeights).filter(RatingWeights.user_id == profile_id).delete()
            db.commit()

        stmt = select(
            DatingProfile.id,
            func.coalesce(func.array_agg(func.distinct(ProfileInterests.interest_id)), null()).label('interest_ids'),
            func.coalesce(func.array_agg(func.distinct(ProfileGenreMusic.sub_genre_music_id)), null()).label('genre_music_ids'),
            func.coalesce(func.array_agg(func.distinct(ProfileFacts.subfacts_id)), null()).label('facts_ids'),
            DatingProfile.education,
            DatingProfile.work,
            DatingProfile.films,
            DatingProfile.book,
            DatingProfile.about,
        ).outerjoin(ProfileInterests, DatingProfile.id == ProfileInterests.dating_profile_id) \
        .outerjoin(ProfileGenreMusic, DatingProfile.id == ProfileGenreMusic.dating_profile_id) \
        .outerjoin(ProfileFacts, DatingProfile.id == ProfileFacts.dating_profile_id) \
        .where(DatingProfile.id != profile_id) \
        .group_by(DatingProfile.id, 
                DatingProfile.education, 
                DatingProfile.work,
                DatingProfile.films,
                DatingProfile.book,
                DatingProfile.about)

        all_profile = db.execute(stmt).fetchall()

        for item in all_profile:
            logging.info(f'TOTAL PROFILES FOUND {len(all_profile)} ==== ID {item.id}')

        interest_names = db.execute(select(Interests.id, Interests.interest_name)).fetchall()
        genre_music_names = db.execute(select(GenreMusic.id, GenreMusic.genre_music_name)).fetchall()
        facts_names = db.execute(select(Facts.id, Facts.facts_name)).fetchall()

        interest_name_dict = {id: name for id, name in interest_names}
        genre_music_name_dict = {id: name for id, name in genre_music_names}
        facts_name_dict = {id: name for id, name in facts_names}


        logging.info(all_profile)

        for row in all_profile:
            subject_id = row[0]
            interest_ids = row[1]
            genre_music_ids = row[2]
            facts_ids = row[3]
            education = row[4]
            work = row[5]
            films = row[6]
            book = row[7]
            about = row[8]
            
            interests = [interest_name_dict.get(id, "Unknown Interest") for id in interest_ids]
            genre_music = [genre_music_name_dict.get(id, "Unknown Genre") for id in genre_music_ids]
            facts = [facts_name_dict.get(id, "Unknown Fact") for id in facts_ids]
            
            interest_rate = sum(interests_relevance.get(letter, 0) for name in interests for letter in name.lower())
            genre_music_rate = sum(genre_music_relevance.get(letter, 0) for name in genre_music for letter in name.lower())
            facts_rate = sum(facts_relevance.get(letter, 0) for name in facts for letter in name.lower())
            education_rate = sum(education_relevance.get(name, 0) for name in education.lower())
            work_rate = sum(work_relevance.get(name, 0) for name in work.lower())
            films_rate = sum(films_relevance.get(name, 0) for name in films.lower())
            book_rate = sum(book_relevance.get(name, 0) for name in book.lower())
            about_rate = sum(about_relevance.get(name, 0) for name in about.lower())
            
            total = interest_rate + genre_music_rate + facts_rate + education_rate + work_rate + films_rate + book_rate + about_rate

            if display:
                logging.info(f"""
        Profile: {subject_id}
        ----
        Interests({interest_ids}): {interest_rate}
        Genre Music({genre_music_ids}): {genre_music_rate}
        Facts({facts_ids}): {facts_rate}
        Education({education}): {education_rate}
        Work({work}): {work_rate}            
        Films({films}): {films_rate}            
        Book({book}): {book_rate}            
        About({about}): {about_rate}            
        -----
        Total: {total}
        """)

            if save:
                new_rating = RatingWeights(
                    user_id=profile_id,
                    profile_id=subject_id,
                    interest_weight=interest_rate,
                    genre_music_weight=genre_music_rate,
                    facts_weight=facts_rate,
                    education_weight=education_rate,
                    work_weight=work_rate,
                    films_weight=films_rate,
                    book_weight=book_rate,
                    about_weight=about_rate,
                    total_weights=total
                )
                db.add(new_rating)
                db.commit()

        return {
            'interests_relevance': interests_relevance,
            'genre_music_relevance': genre_music_relevance,
            'facts_relevance': facts_relevance,
            'education_relevance': education_relevance,
            'work_relevance': work_relevance
        }
    
    def _recalculate_weights(self,
            # db: Session = Depends(deps.get_db),
    ):
        db = next(deps.get_db())
        try:
            dating_profiles = db.query(DatingProfile).all()
            for profile in dating_profiles:
                feedback = self._rates_analyze(profile.id, save=True, display=False, db=db)
            if feedback:
                logging.info('The setting of the scales was successful!!!')
            else:
                logging.info('The setting of the scales was successful!!!')
        finally:
            db.close()

    def _add_other_models_for_dating_profile(
        self,
        db: Session,
        obj_in: T,
        user: User,
        model: Type[T],
        profile_relation_model: Type[ProfileInterests],
        id_field_name: str,
    ) -> List[T]:
        
        db.query(profile_relation_model).filter(
            profile_relation_model.dating_profile_id == user.dating_profile.id
        ).delete()

        created_objects = []
        for item_id in obj_in.id:
           
            item = db.query(model).filter(model.id == item_id).first()
            if not item:
                continue
                # raise UnfoundEntity(message=f"{model.__name__} с идентификатором {item_id} не существует")

            db_user_item = profile_relation_model(
                dating_profile_id=user.dating_profile.id, **{id_field_name: item_id}
            )
            db.add(db_user_item)
            created_objects.append(db_user_item)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

        for db_user_item in created_objects:
            db.refresh(db_user_item)

        return created_objects
    
    def _delete_old_like(self, db: Session, current_dating_profile: DatingProfile):
        now = func.now()
        seven_days_ago = now - timedelta(days=7)

        old_likes = (db.query(ProfileLike).filter(
            ProfileLike.liker_dating_profile_id == current_dating_profile.id,
            ProfileLike.created.isnot(None),
            ProfileLike.mutual.is_(False),
            ProfileLike.created <= seven_days_ago
        ).all())
        for like in old_likes:
            db.delete(like)
        db.commit()

    def upload_image_to_s3(
        self, db: Session, db_obj: DatingProfile, image: UploadFile
    ) -> Optional[ProfileAvatar]:
        host = self.s3_client._endpoint.host
        bucket_name = self.s3_bucket_name
        url_prefix = host + "/" + bucket_name + "/"
        name = (
            "dating_profile/images/"
            + uuid.uuid4().hex
            + os.path.splitext(image.filename)[1]
        )
        new_url = url_prefix + name

        result = self.s3_client.put_object(
            Bucket=bucket_name,
            Key=name,
            Body=image.file,
            ContentType=image.content_type,
        )

        if not (
            200 <= result.get("ResponseMetadata", {}).get("HTTPStatusCode", 500) < 300
        ):
            return None

        avatar = ProfileAvatar()
        avatar.dating_profile_id = db_obj.id
        avatar.url = new_url
        db.add(avatar)
        db.commit()
        db.refresh(avatar)

        return avatar

    def create_with_user(
        self, db: Session, *, obj_in: CreatingDatingProfile, user: User
    ) -> GettingDatingProfile:
        # obj_in_data = obj_in.dict(exclude_unset=True)
        db_obj = DatingProfile(
            user_id=user.id,
            films=obj_in.films,
            book=obj_in.book,
            about=obj_in.about,
            education=obj_in.education,
            work=obj_in.work,
            relationship_type=obj_in.relationship_type
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Обновляем поле is_dating_profile в модели User
        user.is_dating_profile = True
        db.add(user)
        db.commit()
        db.refresh(user)

        if obj_in.sub_interest_id:
            sub_interest_obj = AddUserProfilSubInterest(id=obj_in.sub_interest_id)
            self._add_other_models_for_dating_profile(
                db=db,
                obj_in=sub_interest_obj,
                user=user,
                model=Interests,
                profile_relation_model=ProfileInterests,
                id_field_name="interest_id",
            )

        if obj_in.sub_facts_id:
            sub_facts_obj = AddUserProfilSubFacts(id=obj_in.sub_facts_id)
            self._add_other_models_for_dating_profile(
                db=db,
                obj_in=sub_facts_obj,
                user=user,
                model=Facts,
                profile_relation_model=ProfileFacts,
                id_field_name="subfacts_id",
            )

        if obj_in.sub_genre_music_id:
            sub_genre_music_obj = AddUserProfilSubGenreMusic(
                id=obj_in.sub_genre_music_id
            )
            self._add_other_models_for_dating_profile(
                db=db,
                obj_in=sub_genre_music_obj,
                user=user,
                model=GenreMusic,
                profile_relation_model=ProfileGenreMusic,
                id_field_name="sub_genre_music_id",
            )

        return db_obj

    def update_dating_profile(
        self,
        db: Session,
        *,
        user: User,
        db_obj: DatingProfile,
        obj_in: Union[UpdatingDatingProfile, Dict[str, Any]],
    ) -> GettingDatingProfile:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        if "sub_interest_id" in update_data:
            sub_interest_obj = AddUserProfilSubInterest(
                id=update_data["sub_interest_id"]
            )
            self._add_other_models_for_dating_profile(
                db=db,
                obj_in=sub_interest_obj,
                user=user,
                model=Interests,
                profile_relation_model=ProfileInterests,
                id_field_name="interest_id",
            )

        if "sub_facts_id" in update_data:
            sub_facts_obj = AddUserProfilSubFacts(id=update_data["sub_facts_id"])
            self._add_other_models_for_dating_profile(
                db=db,
                obj_in=sub_facts_obj,
                user=user,
                model=Facts,
                profile_relation_model=ProfileFacts,
                id_field_name="subfacts_id",
            )

        if "sub_genre_music_id" in update_data:
            sub_genre_music_obj = AddUserProfilSubGenreMusic(
                id=update_data["sub_genre_music_id"]
            )
            self._add_other_models_for_dating_profile(
                db=db,
                obj_in=sub_genre_music_obj,
                user=user,
                model=GenreMusic,
                profile_relation_model=ProfileGenreMusic,
                id_field_name="sub_genre_music_id",
            )

        return db_obj

    def add_dating_profile_photo(
        self, db: Session, *, db_obj: DatingProfile, images: List[UploadFile]
    ):
        for image in images:
            self.upload_image_to_s3(db, db_obj, image)

        return

    def get_image_by_id(self, db: Session, id: Any):
        return db.query(ProfileAvatar).filter(ProfileAvatar.id == id).first()

    def delete_image(self, db: Session, *, image: ProfileAvatar) -> None:
        db.delete(image)
        db.commit()

    def delete_dating_profile(self, db: Session, user: User):
        if user.dating_profile is not None:
            dating_profile = user.dating_profile

            user.is_dating_profile = False

            db.add(user)

            db.delete(dating_profile)
            db.commit()
            db.refresh(user)
        else:
            raise UnfoundEntity(message="У пользователя нет профиля для знакомств")
        

    def get_search_dating_profiles(
        self,
        db: Session,
        user: User,
        page: Optional[int] = None,
        per_page: int = 30,
        gender_filter: int = None,
        age_filter_min: int = None,
        age_filter_max: int = None,
        relationship_type_filter: int = None,
    ) -> Tuple[List[dict], dict]:

        
        current_dating_profile = user.dating_profile

        # Making the old likes longer
        self._delete_old_like(db=db, current_dating_profile=current_dating_profile)
        
        weights_subquery = db.query(
            RatingWeights.profile_id,
            RatingWeights.total_weights
        ).filter(RatingWeights.user_id == current_dating_profile.id).subquery()

        weights_alias = aliased(weights_subquery)

        query = db.query(DatingProfile).outerjoin(
            weights_alias,
            DatingProfile.id == weights_alias.c.profile_id
        ).filter(
            DatingProfile.id != current_dating_profile.id
        )

        liked_profiles = (
            db.query(ProfileLike.liked_dating_profile_id)
            .filter(ProfileLike.liker_dating_profile_id == current_dating_profile.id )
            .subquery()
        )

        liked_profiles_select = select([liked_profiles.c.liked_dating_profile_id])

        query = query.filter(DatingProfile.id.notin_(liked_profiles_select))

        
        user_alias_1 = aliased(User)
        user_alias_2 = aliased(User)

        if gender_filter is not None:
            gender_filter_str = Gender(gender_filter)
            if gender_filter_str is not None:
                query = query.join(user_alias_1, user_alias_1.id == DatingProfile.user_id).filter(user_alias_1.gender == gender_filter_str)

        if age_filter_min is not None and age_filter_max is not None:
            query = query.join(user_alias_2, user_alias_2.id == DatingProfile.user_id).filter(
                extract('year', func.age(user_alias_2.birthtime)) >= age_filter_min,
                extract('year', func.age(user_alias_2.birthtime)) <= age_filter_max
            )
        elif age_filter_min is not None:
            query = query.join(user_alias_2, user_alias_2.id == DatingProfile.user_id).filter(extract('year', func.age(user_alias_2.birthtime)) >= age_filter_min)
        elif age_filter_max is not None:
            query = query.join(user_alias_2, user_alias_2.id == DatingProfile.user_id).filter(extract('year', func.age(user_alias_2.birthtime)) <= age_filter_max)

        if relationship_type_filter is not None:
            relationship_type_str = RelationshipType(relationship_type_filter)
            query = query.filter(DatingProfile.relationship_type == relationship_type_str)

        query = query.order_by(weights_alias.c.total_weights.desc().nullslast())
        
        return pagination.get_page(query, page)

    def save_like(self, db: Session, user: User, data: LikeDisLikeDatingProfile) -> ProfileLike:
        # We check if there is already a like or dislike
        existing_like = db.query(ProfileLike).filter(
            ProfileLike.liker_dating_profile_id == user.dating_profile.id,
            ProfileLike.liked_dating_profile_id == data.profile_id
        ).first()

        mutual_like_exists = db.query(ProfileLike).filter(
            ProfileLike.liker_dating_profile_id == data.profile_id,
            ProfileLike.liked_dating_profile_id == user.dating_profile.id,
            ProfileLike.like == True  
        ).first()
        if existing_like:
            if not data.like:
                existing_like.like = data.like
                existing_like.mutual = False
                db.commit()
                if mutual_like_exists:
                    mutual_like_exists.mutual = False
                    db.add(mutual_like_exists)
                return None
            else:
                if existing_like.like == data.like:
                    raise HTTPException(status_code=400, detail="Ошибка, отметак нравится отправлена повторно")
                existing_like.like = data.like
                existing_like.liker_estimate_type = data.liker_estimate_type
                existing_like.mutual = mutual_like_exists is not None
                if mutual_like_exists:
                    mutual_like_exists.mutual = True
                    db.add(mutual_like_exists)
                db.commit()
                db.refresh(existing_like)
                return existing_like

        new_like = ProfileLike(
            liker_dating_profile_id=user.dating_profile.id,
            liked_dating_profile_id=data.profile_id,
            like=data.like,
            liker_estimate_type=data.liker_estimate_type,
            mutual=mutual_like_exists is not None
        )
        if mutual_like_exists:
            mutual_like_exists.mutual = True
            db.add(mutual_like_exists)
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return new_like


    def get_like_dating_profile(self, db: Session, current_user: User, page: Optional[int] = None,
                                per_page: int = 30,) -> List[ProfileLike]:
        query = db.query(ProfileLike).filter(
            and_(
                ProfileLike.liked_dating_profile_id == current_user.dating_profile.id,
                ProfileLike.like == True,
                ProfileLike.mutual == False
            )
        )
        return pagination.get_page(query, page)
    
    def get_mutual_dating_profile(self, db: Session, 
                                  current_user: User, 
                                  page: Optional[int] = None,
                                per_page: int = 30,
        ) -> List[ProfileLike]:
        query = db.query(ProfileLike).filter(
            and_(
                or_(
                    ProfileLike.liked_dating_profile_id == current_user.dating_profile.id,
                    ProfileLike.liker_dating_profile_id == current_user.dating_profile.id
                ),
                ProfileLike.like == True,
                ProfileLike.mutual == True
            )
        )
        return pagination.get_page(query, page)




    def fake_db(self, db: Session, quantity: int):
        first_names = [
            "Joh3n", "Jane", "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi",
            "Ivan", "Julia", "Kevin", "Linda", "Mike", "Nancy", "Oscar", "Patty", "Quincy", "Rachel",
            "Steve", "Tina", "Ulysses", "Vicky", "Walter", "Xena", "Yvonne", "Zack", "Anna", "Ben",
            "Cathy", "Dennis", "Elaine", "Fred", "Gina", "Harry", "Irene", "Jack", "Kelly", "Larry",
            "Maggie", "Nick", "Olivia", "Paul", "Queenie", "Rob", "Sandy", "Tom", "Uma", "Vince"
        ]
        last_names = [
            "Smit3h", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
            "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
        ]
        emails = [
            "joh3n.smith@example.com", "jane.johnson@example.com", "alice.williams@example.com", "bob.brown@example.com", "charlie.jones@example.com",
            "david.garcia@example.com", "eve.miller@example.com", "frank.davis@example.com", "grace.rodriguez@example.com", "heidi.martinez@example.com",
            "ivan.hernandez@example.com", "julia.lopez@example.com", "kevin.gonzalez@example.com", "linda.wilson@example.com", "mike.anderson@example.com",
            "nancy.thomas@example.com", "oscar.taylor@example.com", "patty.moore@example.com", "quincy.jackson@example.com", "rachel.martin@example.com",
            "steve.lee@example.com", "tina.perez@example.com", "ulysses.thompson@example.com", "vicky.white@example.com", "walter.harris@example.com",
            "xena.sanchez@example.com", "yvonne.clark@example.com", "zack.ramirez@example.com", "anna.lewis@example.com", "ben.robinson@example.com",
            "cathy.walker@example.com", "dennis.young@example.com", "elaine.allen@example.com", "fred.king@example.com", "gina.wright@example.com",
            "harry.scott@example.com", "irene.torres@example.com", "jack.nguyen@example.com", "kelly.hill@example.com", "larry.flores@example.com",
            "maggie.green@example.com", "nick.adams@example.com", "olivia.nelson@example.com", "paul.baker@example.com", "queenie.hall@example.com",
            "rob.rivera@example.com", "sandy.campbell@example.com", "tom.mitchell@example.com", "uma.carter@example.com", "vince.roberts@example.com"
        ]
        tels = [
            "796132223", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222",
            "796132222", "796142222", "796142222", "796142222", "796142222"
        ]
        genders = ["male", "female"]

        films = [
            "The Shawshank Redemption", "The Godfather", "The Dark Knight", "Pulp Fiction", "Fight Club",
            "Inception", "The Matrix", "Forrest Gump", "The Lord of the Rings", "Star Wars",
            "The Avengers", "Jurassic Park", "Titanic", "Gladiator", "Avatar",
            "The Lion King", "Toy Story", "The Silence of the Lambs", "The Departed", "The Green Mile",
            "Schindler's List", "Saving Private Ryan", "Goodfellas", "Casablanca", "The Wizard of Oz",
            "Gone with the Wind", "The Terminator", "Alien", "Blade Runner", "The Big Lebowski",
            "The Social Network", "Black Swan", "Whiplash", "La La Land", "Get Out",
            "Parasite", "Joker", "1917", "Tenet", "Memento",
            "The Prestige", "Inglourious Basterds", "Django Unchained", "The Grand Budapest Hotel", "Moonlight",
            "Birdman", "The Shape of Water", "Mad Max: Fury Road", "Spider-Man: Into the Spider-Verse", "The Irishman"
        ]

        book = [
            "To Kill a Mockingbird", "1984", "Pride and Prejudice", "The Great Gatsby", "Moby Dick",
            "War and Peace", "The Catcher in the Rye", "One Hundred Years of Solitude", "Brave New World", "The Odyssey",
            "Crime and Punishment", "The Brothers Karamazov", "Anna Karenina", "Don Quixote", "The Divine Comedy",
            "Madame Bovary", "Wuthering Heights", "Jane Eyre", "Great Expectations", "Middlemarch",
            "The Adventures of Huckleberry Finn", "Les Misérables", "The Count of Monte Cristo", "Dracula", "Frankenstein",
            "The Picture of Dorian Gray", "The Scarlet Letter", "The Grapes of Wrath", "To the Lighthouse", "Slaughterhouse-Five",
            "Catch-22", "One Flew Over the Cuckoo's Nest", "Beloved", "The Color Purple", "The Handmaid's Tale",
            "The Road", "The Kite Runner", "Life of Pi", "The Alchemist", "The Book Thief",
            "The Goldfinch", "The Night Circus", "The Martian", "The Girl with the Dragon Tattoo", "The Help"
        ]

        about = [
            "I love hiking and exploring nature.", "I enjoy reading classic literature.", "I'm passionate about photography.",
            "I love cooking and trying new recipes.", "I enjoy playing guitar and writing songs.", "I'm a big fan of science fiction movies.",
            "I love traveling and experiencing new cultures.", "I enjoy playing video games in my free time.", "I'm passionate about painting and drawing.",
            "I love spending time with my family and friends.", "I enjoy watching documentaries on various topics.", "I'm a big fan of jazz music.",
            "I love gardening and growing my own vegetables.", "I enjoy practicing yoga and meditation.", "I'm passionate about learning new languages.",
            "I love going to the beach and surfing.", "I enjoy playing basketball with my friends.", "I'm a big fan of classic rock music.",
            "I love cooking Italian food and trying new recipes.", "I enjoy playing chess and solving puzzles.", "I'm passionate about history and ancient civilizations.",
            "I love hiking and exploring national parks.", "I enjoy reading mystery novels and solving puzzles.", "I'm a big fan of horror movies and books.",
            "I love dancing and attending dance classes.", "I enjoy playing soccer and watching matches.", "I'm passionate about astronomy and space exploration.",
            "I love cooking French cuisine and trying new recipes.", "I enjoy playing tennis and staying active.", "I'm a big fan of classical music and opera.",
            "I love traveling and exploring different countries.", "I enjoy reading fantasy novels and escaping into other worlds.", "I'm passionate about environmental conservation.",
            "I love cooking Mexican food and trying new recipes.", "I enjoy playing golf and spending time outdoors.", "I'm a big fan of indie films and documentaries."
        ]

        education = [
            "Bachelor's Degree in Computer Science", "Master's Degree in Business Administration", "PhD in Physics",
            "Bachelor's Degree in Psychology", "Master's Degree in Education", "PhD in Chemistry",
            "Bachelor's Degree in Engineering", "Master's Degree in Public Health", "PhD in Biology",
            "Bachelor's Degree in Economics", "Master's Degree in Social Work", "PhD in Mathematics",
            "Bachelor's Degree in History", "Master's Degree in Fine Arts", "PhD in Philosophy",
            "Bachelor's Degree in English Literature", "Master's Degree in Journalism", "PhD in Sociology",
            "Bachelor's Degree in Environmental Science", "Master's Degree in Architecture", "PhD in Geology",
            "Bachelor's Degree in Political Science", "Master's Degree in Law", "PhD in Anthropology",
            "Bachelor's Degree in Communications", "Master's Degree in Public Policy", "PhD in Linguistics",
            "Bachelor's Degree in Nursing", "Master's Degree in Healthcare Administration", "PhD in Medicine",
            "Bachelor's Degree in Marketing", "Master's Degree in Human Resources", "PhD in Business Administration",
            "Bachelor's Degree in Information Technology", "Master's Degree in Data Science", "PhD in Cybersecurity",
            "Bachelor's Degree in Graphic Design", "Master's Degree in Creative Writing", "PhD in Film Studies",
            "Bachelor's Degree in Music", "Master's Degree in Theater Arts", "PhD in Performance Studies"
        ]

        work = [
            "Software Engineer", "Data Scientist", "Project Manager", "Marketing Specialist", "Financial Analyst",
            "Human Resources Manager", "Sales Representative", "Customer Service Representative", "Graphic Designer", "Web Developer",
            "Systems Administrator", "Network Engineer", "Cybersecurity Analyst", "Database Administrator", "Business Analyst",
            "Operations Manager", "Supply Chain Manager", "Logistics Coordinator", "Quality Assurance Specialist", "Product Manager",
            "UX/UI Designer", "Content Writer", "Social Media Manager", "Public Relations Specialist", "Event Planner",
            "Executive Assistant", "Administrative Assistant", "Office Manager", "Legal Assistant", "Paralegal",
            "Teacher", "Professor", "School Counselor", "Librarian", "Principal",
            "Nurse", "Physician", "Dentist", "Pharmacist", "Physical Therapist",
            "Veterinarian", "Architect", "Civil Engineer", "Mechanical Engineer", "Electrical Engineer",
            "Chef", "Restaurant Manager", "Bartender", "Waiter/Waitress", "Culinary Chef"
        ]

        sub_interest_id = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
        sub_facts_id = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
        sub_genre_music_id = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36 , 37, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 63, 65, 66, 67, 68, 69]

        for i in range(quantity):  
            user = User(
                first_name=first_names[random.randint(1, 48)],
                patronymic=first_names[random.randint(1, 48)],  
                last_name=last_names[random.randint(1, 48)],
                email=emails[random.randint(1, 48)] + str(random.randint(10, 99)),
                tel=tels[random.randint(1, 48)] + str(random.randint(10, 99)),
                birthtime=datetime.now() - timedelta(days=365 * (18 + i % 47)),
                hashed_password='$2b$12$0By1d/PUEkie1lF0Vms0u.4gE9MSarUeheTQ8326wqfo9FCGd94tW',
                is_active=True,
                is_superuser=False,
                gender=genders[random.randint(0, 1)],
                region=0,
                created_orders_count=0,
                completed_orders_count=0,
                my_offers_count=0,
                subscriptions_count=0,
                subscribers_count=0,
            )
            db.add(user)
            db.commit()

            if user:
                logging.info(f'Пользователь создался успешно, ID {user.id}')

            create_dating = CreatingDatingProfile(
                films=films[random.randint(1, len(films))],
                book= book[random.randint(1, len(book))],
                about= about[random.randint(1, len(about))],
                education= education[random.randint(1, len(education))],
                work= work[random.randint(1, len(work))],
                relationship_type= random.randint(0, 2),
                sub_interest_id=random.sample(sub_interest_id, 2),
                sub_facts_id=random.sample(sub_facts_id, 2),
                sub_genre_music_id=random.sample(sub_genre_music_id, 2),
            )

            res_dating_profile = self.create_with_user(db=db, obj_in=create_dating, user=user)
            if res_dating_profile:
                logging.info(f'Профиль занкомств создался успешно, ID {res_dating_profile.id}')
                logging.info(res_dating_profile)




dating_profile = CRUDDatingProfile(DatingProfile)
