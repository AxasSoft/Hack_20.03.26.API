import enum

class RestaurantType(str, enum.Enum):
    RESTAURANT = "restaurant"
    BAR = "bar"
    CAFE = "cafe"