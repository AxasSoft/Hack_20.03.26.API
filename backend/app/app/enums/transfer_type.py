import enum

# class DescriptiveEnum(str, enum.Enum):
#     """Базовый Enum с описаниями для Swagger."""
#
#     @property
#     def description(self) -> str:
#         raise NotImplementedError
#
#     def __str__(self):
#         return self.value

class TransferType(str, enum.Enum):
    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"
    VIP = "vip"
    MINIVAN = "minivan"

    # def __new__(cls, value: int, description: str):
    #     obj = object.__new__(cls)
    #     obj._value_ = value
    #     obj.description = description
    #     return obj

    @property
    def description(self) -> str:
        return {
            TransferType.ECONOMY: "Стандартный эконом-класс",
            TransferType.COMFORT: "Повышенный комфорт",
            TransferType.BUSINESS: "Бизнес-класс",
            TransferType.VIP: "VIP-обслуживание",
            TransferType.MINIVAN: "Минивэн",
        }[self]
