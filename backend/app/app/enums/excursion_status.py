import enum

class ExcursionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"