from typing import Optional, List

from pydantic import BaseModel, Field, validator

# from . import GettingExcursionCategory, GettingExcursionReview
from .id_model import IdModel
from .audio import GettingAudio
from ..enums.mod_status import ModStatus


class MultilineString(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            return v.replace('\r\n', '\n')
        raise ValueError("Must be a string")

class BaseAudioGuide(BaseModel):
    title: str
    description: Optional[MultilineString] = None
    lat: Optional[float]
    lon: Optional[float]


class CreatingAudioGuide(BaseAudioGuide):
    pass



class UpdatingAudioGuide(BaseAudioGuide):
    pass


class GettingAudioGuide(IdModel, CreatingAudioGuide):
    audios: List[GettingAudio]
    created: int
