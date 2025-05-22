import enum

class HotelBookingStatus(str, enum.Enum):
    NEW = "new"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    COMPLETED = "completed"
    PROCESSING = "processing"
    API_ERROR = "api_error"
    PAY_ERROR = "pay_error"