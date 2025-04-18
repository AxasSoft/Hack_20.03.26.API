import enum

class ExcursionBookingStatus(str, enum.Enum):
    # UNPAID = "unpaid"
    # PREPAYMENT = "prepayment"
    # PAID_CANCELED = "paid_canceled"
    # PREPAYMENT_CANCELED = "prepayment_canceled"
    # CANCELED = "canceled"
    NEW = "new"
    PAID = "paid"
    REJECTED = "rejected"
    FINISHED = "finished"