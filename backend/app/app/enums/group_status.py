import enum

class GroupStatus(enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    COMPLETED = "COMPLETED"
    FREE = "FREE"