import enum

class TransferType(enum.Enum):
    ECONOMY = "economy", 'Стандартный эконом-класс'
    COMFORT = "comfort", 'Повышенный комфорт'
    BUSINESS = "business", 'Бизнес-класс'
    VIP = "vip", 'VIP-обслуживание'
    MINIVAN = "minivan", 'Минивэн'

    def __new__(cls, value: int, description: str):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj