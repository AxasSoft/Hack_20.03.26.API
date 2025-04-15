import enum

class GroupStatus(enum.Enum):
    AVAILABLE = "available"
    REGISTRATION = "registration"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"