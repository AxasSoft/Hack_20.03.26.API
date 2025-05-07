import enum

class GroupStatus(str, enum.Enum):
    AVAILABLE = "available"
    COMPLETED = "completed"
    FINISHED = "finished"