import datetime
from functools import lru_cache
from typing import Generator, Optional

import boto3
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy import create_engine, engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.schemas.response import BaseResponse, ListOfEntityResponse, SingleEntityResponse
from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.models import User

from ..notification.consumers import FireBaseConsumer, TerminalConsumer, DbConsumer
from ..notification.notificator import Notificator

from app.utils.cache import Cache
from ..services.gsms_tg_sender.base_gsms_tg_sender import BaseTgSender
from ..services.gsms_tg_sender.gsms_tg_sender import GsmsTgSender

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

optional_reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False
)


# def get_db() -> Generator:
#     db = None
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         if db is not None:
#             db.close()


@lru_cache()
def get_engine() -> engine.Engine:
    return create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        # connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True,
        poolclass=QueuePool,
        pool_size=50,
        max_overflow=50
    )


def get_db() -> Generator[Session, None, None]:
    # Explicit type because sessionmaker.__call__ stub is Any
    session: Session = sessionmaker(
        autocommit=False, autoflush=False,expire_on_commit=False, bind=get_engine()
    )()
    # session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def update_visit_date(db: Session, user: User):
    user.last_visited = datetime.datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM], options={
                'verify_exp': 'exp' in settings.TOKEN_CHECKS,
                'verify_nbf': 'nbf' in settings.TOKEN_CHECKS,
            }
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud.user.get_by_id(db, id=token_data.sub)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.deleted is not None:
        raise HTTPException(status_code=404, detail="User not found")
    update_visit_date(db=db, user=user)
    return user


def get_optional_current_user(
    db: Session = Depends(get_db), token: str = Depends(optional_reusable_oauth2)
) -> Optional[models.User]:
    if token is None:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM], options={
                'verify_exp': 'exp' in settings.TOKEN_CHECKS,
                'verify_nbf': 'nbf' in settings.TOKEN_CHECKS,
            }
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud.user.get_by_id(db, id=token_data.sub)
    if user is None or user.deleted is not None:
        raise HTTPException(status_code=404, detail="User not found")

    update_visit_date(db=db, user=user)
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_active_support(
        current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user) and not current_user.is_support:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_bucket_name() -> str:
    return settings.S3_BUCKET_NAME


def get_s3_client():
    session = boto3.session.Session()
    s3 = session.client(
        service_name=settings.S3_SERVICE_NAME,
        endpoint_url=settings.S3_ENDPOINTS_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    )

    return s3





def get_notificator() -> Notificator:
    notificator = Notificator()
    notificator.consumers = [
        TerminalConsumer(),
        DbConsumer(),
        FireBaseConsumer(),
    ]
    return notificator


def get_redis():
    redis_instance = redis.StrictRedis(
        host='85.92.111.28',
        port=6379,
        password='Ah%\no4{WKi\m(',
        username='default'
    )
    return redis_instance


# def get_redis():
#     return redis.Redis.from_url(
#         settings.REDIS_URL,
#     )


def get_cache_sing(redis_instance=Depends(get_redis)):
    return Cache(redis=redis_instance, response_schema=SingleEntityResponse, ttl=settings.CACHE_TTL)


def get_cache_list(redis_instance=Depends(get_redis)):
    return Cache(redis=redis_instance, response_schema=ListOfEntityResponse, ttl=settings.CACHE_TTL)

def get_cache_no_depends():
    return Cache(
        redis=get_redis(), response_schema=BaseResponse, ttl=settings.CACHE_TTL
    )

def get_gsms_tg_sender() -> BaseTgSender:
    return GsmsTgSender()


