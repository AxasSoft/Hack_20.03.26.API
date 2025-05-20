import enum

class HotelBookingStatus(str, enum.Enum):
    NEW = "new"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    COMPLETED = "completed"