import json
import logging
from typing import Optional, List
import requests
import base64
from requests.auth import HTTPBasicAuth
import os

from app.core.config import settings
from app.utils.security import generate_random_password
from app.exceptions import UnprocessableEntity
from app.schemas.hotel import RoomGuests, GettingHotelSearchInfo
from app.utils.datetime import from_unix_timestamp
from app.utils.pagination import get_page_no_db
from fastapi import HTTPException

from app.core.config import settings

DUMP_PATH = "geogesh_hotels.json"
BASE_COMFORT = {
    "Трансфер": "transfer",
    "Парковка": "parking",
    "Животные": "animals",
    "Интернет": "internet",
    "Бассейн и пляж": "pool"
}

class ETGOstrovokManager:
    KEY_ID = 12427
    API_KEY = "c67b8178-0c9d-4760-a826-b61a46b81c1c"
    def __init__(self):
        self.region_id = 965821545
        self.search_by_region_url = "https://api.worldota.net/api/b2b/v3/search/serp/region/"
        self.encoded_credentials = base64.b64encode(f"{self.KEY_ID}:{self.API_KEY}".encode("ascii")).decode("ascii")

    def parse_guests_query(self, guests_str: str) -> List[RoomGuests]:
        try:
            rooms = []
            for room_str in guests_str.split("-"):
                parts = room_str.split("and")
                adults = int(parts[0])
                children = list(map(int, parts[1].split("."))) if len(parts) > 1 else None
                rooms.append(RoomGuests(adults=adults, children=children))
            return rooms
        except Exception as e:
            raise HTTPException(400, f"Invalid format. Expected 'XandY.Z-XandY.Z', got '{guests_str}'. Error: {e}")

    def get_hotels(
            self,
            checkin: int,
            checkout: int,
            # currency: Optional[str] = None,
            # hotels_limit: Optional[int] = None,
            # language: Optional[str] = None,
            # guests: Optional[List[RoomGuests]],
            guests: Optional[str],
            page: Optional[int] = None
    ):
        checkin_date = str(from_unix_timestamp(checkin).date())
        checkout_date = str(from_unix_timestamp(checkout).date())
        gest_list = self.parse_guests_query(guests)
        payload = {
            "checkin": checkin_date,
            "checkout": checkout_date,
            "region_id": self.region_id,
        }
        if guests:
            payload["guests"] = [
                guest.dict(exclude_unset=True) for guest in gest_list
            ]
        logging.info("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            self.search_by_region_url,
            # auth=HTTPBasicAuth(settings.ETG_KEY_ID, settings.ETG_API_KEY),
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        hotels_hids = []
        hotels_getting_data = {}  # {'hid': data_obj}
        for available_hotel in response["data"]["hotels"]:
            hotels_hids.append(available_hotel["hid"])
            hotel_getting_data = GettingHotelSearchInfo()
            hotel_getting_data.hid = available_hotel["hid"]

            first_rate = available_hotel["rates"][0]
            first_rate_payment = first_rate["payment_options"]["payment_types"][0]

            hotel_getting_data.meal_included = False if first_rate["meal_data"]["value"] == "nomeal" else True
            hotel_getting_data.card_payment = True if first_rate_payment["by"] == "credit_card" else False
            hotel_getting_data.free_cancellation = True if first_rate_payment["cancellation_penalties"]["free_cancellation_before"] \
                else False
            hotel_getting_data.room_name = first_rate["room_name"]
            hotel_getting_data.price = first_rate_payment["show_amount"]
            hotel_getting_data.currency = first_rate_payment["currency_code"]

            hotels_getting_data[available_hotel["hid"]] = hotel_getting_data

        # Получение информации из дампа
        try:
            with open(DUMP_PATH, "r", encoding="utf-8") as file:
                for line in file:
                    hotel_data = json.loads(line.strip())
                    if hotel_data.get("hid") in hotels_hids:
                        obj = hotels_getting_data[hotel_data.get("hid")]
                        obj.address = hotel_data.get("address")
                        obj.name = hotel_data.get("name")
                        image_url = hotel_data.get("images")[0].replace('{size}', '1024x768')
                        obj.image = image_url
                        'aaa'.replace('s', 'dd')

                        hotel_comfort = []
                        for amenity_group in hotel_data.get("amenity_groups"):
                            if amenity_group.get("group_name") in BASE_COMFORT:
                                hotel_comfort.append(BASE_COMFORT[amenity_group.get("group_name")])
                        obj.comfort = hotel_comfort




        except Exception as e:
            print(e)

        hotel_list = []
        for hid in hotels_hids:
            hotel_list.append(hotels_getting_data[hid])
        data, paginator = get_page_no_db(hotel_list, page)

        return data, paginator

    def raw_get_hotel(
            self,
            hid: int,
            checkin: int,
            checkout: int,
            guests: Optional[str]
    ):
        checkin_date = str(from_unix_timestamp(checkin).date())
        checkout_date = str(from_unix_timestamp(checkout).date())
        gest_list = self.parse_guests_query(guests)
        payload = {
            "checkin": checkin_date,
            "checkout": checkout_date,
            "hid": hid
        }
        if guests:
            payload["guests"] = [
                guest.dict(exclude_unset=True) for guest in gest_list
            ]
        logging.info("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            self.search_by_region_url,
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response



ostrovok_manager = ETGOstrovokManager()




"""Пример отправляемых данных
{
    "checkin": "2025-10-22",
    "checkout": "2025-10-25",
    "residency": "gb",
    "language": "en",
    "guests": [
        {
            "adults": 2,
            "children": []
        }
    ],
    "region_id": 965849721,
    "currency": "EUR"
}"""

