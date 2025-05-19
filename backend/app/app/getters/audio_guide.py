from typing import List

from app.models import AudioGuide
from app.schemas import GettingAudioGuide, GettingAudio
from app.utils.datetime import to_unix_timestamp
from sqlalchemy.orm import Session


def get_audio_guide(audio_guide: AudioGuide) -> GettingAudioGuide:
    return GettingAudioGuide(
        id=audio_guide.id,
        created=to_unix_timestamp(audio_guide.created),
        title=audio_guide.title,
        description=audio_guide.description,
        lat=audio_guide.lat,
        lon=audio_guide.lon,
        audios=[
            GettingAudio(id=audio.id,
                         link=audio.audio)
            for audio in audio_guide.audio_files
        ],
        image=audio_guide.image.image if audio_guide.image else None
    )

