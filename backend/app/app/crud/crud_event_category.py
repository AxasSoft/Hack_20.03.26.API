from typing import Optional, Union, Dict, Any, Type
import os
import uuid
import datetime as dt

from botocore.client import BaseClient
from sqlalchemy import text, alias, func, or_, and_
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.crud.base import CRUDBase
from app.models import User, EventMember, AcceptingStatus, EventImage, EventCategory
from app.models.event import Event
from app.schemas import CreatingEventCategory, UpdatingEventCategory
from app.schemas.event import CreatingEvent, UpdatingEvent
from app.utils import pagination
from app.utils.datetime import from_unix_timestamp




class CRUDEventCategory(CRUDBase[EventCategory, CreatingEventCategory, UpdatingEventCategory]):
    pass


event_category = CRUDEventCategory(EventCategory)