from pydantic import BaseModel

class HoroscopeForOne(BaseModel):
    yesterday: str
    today: str
    tomorrow: str
    tomorrow02: str


class FullHoroscope(BaseModel):
    aries: HoroscopeForOne
    taurus: HoroscopeForOne
    gemini: HoroscopeForOne
    cancer: HoroscopeForOne
    leo: HoroscopeForOne
    virgo: HoroscopeForOne
    libra: HoroscopeForOne
    scorpio: HoroscopeForOne
    sagittarius: HoroscopeForOne
    capricorn: HoroscopeForOne
    aquarius: HoroscopeForOne
    pisces: HoroscopeForOne
