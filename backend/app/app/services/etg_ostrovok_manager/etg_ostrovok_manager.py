import json
import logging
from http.client import responses
import time
import threading
import uuid
from typing import Optional, List, Union
import requests
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.utils.security import generate_random_password
from app.exceptions import UnprocessableEntity, UnfoundEntity
from app.schemas.hotel import (RoomGuests, GettingHotelSearchInfo, GettingHotelBookingInfo, HotelDescriptionChapter,
                               AvailableRoom, HotelComfortChapter, ClientBookingData, PreCreatedBooking,
                               CreatedBooking, BookingUserData, CreatingBooking, GettingBooking, GettingDetailBooking)
from app.schemas.credit_card import CreditCardData, CreditCardWithCvc
from app.utils.datetime import from_unix_timestamp, to_unix_timestamp
from app.utils.pagination import get_page_no_db
from app.models import HotelBooking
from app.enums.hotel_booking_status import HotelBookingStatus
from app import crud

from app.core.config import settings


DUMP_PATH = "geogesh_hotels.json"
BASE_COMFORT = {
    "Трансфер": "transfer",
    "Парковка": "parking",
    "Животные": "animals",
    "Интернет": "internet",
    "Бассейн и пляж": "pool"
}
HOTEL_COMFORT_LIST = ["Бассейн и пляж", "Интернет", "Животные", "Парковка", "Трансфер", "Общее", "Питание", "В номерах"]
PICT_SIZE = '1024x768'

class ETGOstrovokManager:
    KEY_ID = 12427
    API_KEY = "c67b8178-0c9d-4760-a826-b61a46b81c1c"
    def __init__(self):
        self.region_id = 965821545
        self.search_by_region_url = "https://api.worldota.net/api/b2b/v3/search/serp/region/"
        self.encoded_credentials = base64.b64encode(f"{self.KEY_ID}:{self.API_KEY}".encode("ascii")).decode("ascii")

    def _check_status_in_thread(self, partner_order_id: str, stop_event: threading.Event, db: Session):
        """
        Функция, которая будет выполняться в отдельном потоке для проверки статуса.
        """
        print('*****     CHECKING THREAD START    *****')
        booking = crud.hotel_booking.get_by(db=db, partner_order_id=partner_order_id)
        print(booking)
        while not stop_event.is_set():
            print(f'*****     CHECKING booling {booking.id}    *****')
            time.sleep(5)
            check = self.raw_check_booking(partner_order_id=partner_order_id)
            status = check.get("status")

            if status == "ok":
                booking.status = HotelBookingStatus.COMPLETED
                db.add(booking)
                db.commit()
                print('*****     CHECKING STATUS OK    *****')
                stop_event.set()
                return

            if status == "error":
                if check["error"] in ("block", "3ds", "charge"):
                    booking.status = HotelBookingStatus.PAY_ERROR
                    db.commit()
                    print('*****     CHECKING STATUS PAY_ERROR    *****')
                else:
                    booking.status = HotelBookingStatus.API_ERROR
                    db.add(booking)
                    db.commit()
                    print('*****     CHECKING STATUS API_ERROR    *****')
                stop_event.set()
                return

            if status == "3ds":
                self.secure_check(url=check["data"]["data_3ds"]["action_url"], data=check["data"]["data_3ds"]["data"])
                print('*****     MAKE PAYMENT    *****')


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
            guests: Optional[List[RoomGuests]],
            # guests: Optional[str],
            page: Optional[int] = None
    ):
        checkin_date = str(from_unix_timestamp(checkin).date())
        checkout_date = str(from_unix_timestamp(checkout).date())
        # gest_list = self.parse_guests_query(guests)
        payload = {
            "checkin": checkin_date,
            "checkout": checkout_date,
            "region_id": self.region_id,
        }
        if guests:
            payload["guests"] = [
                guest.dict(exclude_unset=True) for guest in guests
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

        hotels_hids = [8473727, ]
        # if in cash:
        # hotels_user_hids = cash
        # hotels_user_hids_page = pafinator
        hotels_getting_data = {}  # {'hid': data_obj}


        # Получение номеров тестового отеля
        payload = {
            "checkin": checkin_date,
            "checkout": checkout_date,
            "id": "test_hotel_do_not_book"
        }
        if guests:
            payload["guests"] = [
                guest.dict(exclude_unset=True) for guest in guests
            ]
        logging.info("Payload for test hotel: %s", payload)
        print("Payload for test hotel: %s", payload)

        test_hotel_response = requests.post(
            "https://api.worldota.net/api/b2b/v3/search/hp/",
            headers=headers,
            json=payload
        ).json()
        if test_hotel_response["data"]["hotels"]:
            test_hotel_api_data = test_hotel_response["data"]["hotels"][0]
            hotel_getting_data = GettingHotelSearchInfo()
            hotel_getting_data.hid = test_hotel_api_data["hid"]

            first_rate = test_hotel_api_data["rates"][0]
            first_rate_payment = first_rate["payment_options"]["payment_types"][0]

            hotel_getting_data.meal_included = False if first_rate["meal_data"]["value"] == "nomeal" else True
            hotel_getting_data.card_payment = True if first_rate_payment["by"] == "credit_card" else False
            hotel_getting_data.free_cancellation = True if first_rate_payment["cancellation_penalties"][
                "free_cancellation_before"] \
                else False
            hotel_getting_data.room_name = first_rate["room_name"]
            hotel_getting_data.price = first_rate_payment["show_amount"]
            hotel_getting_data.currency = first_rate_payment["currency_code"]
            hotels_getting_data[test_hotel_api_data["hid"]] = hotel_getting_data
        else:
            hotels_hids = []

        for available_hotel in response["data"]["hotels"]:
            # if hotels_user_hids_page
            # and available_hotel["hid"] not in hotels_user_hids_page
            # con
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
                        image_url = hotel_data.get("images")[0].replace('{size}', PICT_SIZE)
                        obj.image = image_url

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
            "https://api.worldota.net/api/b2b/v3/search/hp/",
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response

    def raw_prebooking(
            self,
            booking_hash: str
    ):
        payload = {
            "hash": booking_hash
        }
        logging.info("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/prebook/",
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response


    def get_hotel(
            self,
            hid: int,
            checkin: int,
            checkout: int,
            guests: Optional[str]
    ) -> GettingHotelBookingInfo:
        hotel_api_data = self.raw_get_hotel(hid=hid, checkin=checkin, checkout=checkout, guests=guests)["data"]["hotels"][0]
        hotel_dum_data = None
        try:
            with open(DUMP_PATH, "r", encoding="utf-8") as file:
                for line in file:
                    hotel_data = json.loads(line.strip())
                    if hotel_data.get("hid") == hid:
                        hotel_dum_data = hotel_data
        except Exception as e:
            print(e)

        response_info = GettingHotelBookingInfo(
            hid=hid,
            address=hotel_dum_data["address"],
            name=hotel_dum_data["name"],
            lat=hotel_dum_data["latitude"],
            lon=hotel_dum_data["longitude"],
            phone=hotel_dum_data["phone"],
            email=hotel_dum_data["email"]
        )
        hotel_images = []
        for image in hotel_dum_data["images"]:
            hotel_images.append(image.replace('{size}', PICT_SIZE))
        response_info.images = hotel_images

        description = []
        for chapter in hotel_dum_data["description_struct"]:
            description.append(HotelDescriptionChapter(paragraphs=chapter["paragraphs"], title=chapter["title"]))
        response_info.description = description

        comfort = []
        for amenity_group in hotel_dum_data["amenity_groups"]:
            if amenity_group["group_name"] in HOTEL_COMFORT_LIST:
                comfort.append(HotelComfortChapter(title=amenity_group["group_name"],
                                                   amenities=amenity_group["amenities"]))
        response_info.comfort = comfort


        available_rooms = []
        for room in hotel_api_data["rates"]:
            price = room["payment_options"]["payment_types"][0]["show_amount"]
            is_payment_now = True if room["payment_options"]["payment_types"][0]["type"] == "now" else False
            is_need_credit_card_data = room["payment_options"]["payment_types"][0]["is_need_credit_card_data"]
            free_cancellation_before = room["payment_options"]["payment_types"][0]["cancellation_penalties"]["free_cancellation_before"]
            if free_cancellation_before:
                free_cancellation_before = to_unix_timestamp(
                    datetime.strptime(free_cancellation_before, "%Y-%m-%dT%H:%M:%S"))
            has_free_cancellation = True if free_cancellation_before else False
            room_name = room["room_name"]
            images = []
            for hotel_room in hotel_dum_data["room_groups"]:
                if hotel_room["name"] == room_name:
                    images = [img.replace('{size}', PICT_SIZE) for img in hotel_room["images"]]
            available_rooms.append(AvailableRoom(price=price,
                                                 room_name=room_name,
                                                 images=images,
                                                 book_hash=room["book_hash"],
                                                 match_hash=room["match_hash"],
                                                 is_payment_now=is_payment_now,
                                                 is_need_credit_card_data=is_need_credit_card_data,
                                                 free_cancellation_before=free_cancellation_before,
                                                 has_free_cancellation=has_free_cancellation))
        response_info.available_rooms = available_rooms

        return response_info


    def raw_create_booking(
            self,
            booking_hash: str
    ):
        payload = {
            "partner_order_id": str(uuid.uuid4()),
            "book_hash": booking_hash,
            "language": "ru",
            "user_ip": "109.73.199.21"
        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/booking/form/",
            headers=headers,
            json=payload
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response.json()


    def create_credit_card_token(
            self,
            object_id: str,
            user_first_name: str,
            user_last_name: str,
            pay_uuid: str,
            init_uuid: str,
            credit_card_data: CreditCardWithCvc,
            is_cvc_required: bool
    ):
        payload = {
            "object_id": object_id,
            "pay_uuid": pay_uuid,
            "init_uuid": init_uuid,
            "user_first_name": user_first_name,
            "user_last_name": user_last_name,
            "is_cvc_required": is_cvc_required,
            "credit_card_data_core": {
                "year": credit_card_data.year,
                "card_number": credit_card_data.card_number,
                "card_holder": credit_card_data.card_holder,
                "month": credit_card_data.month,
            },
            "cvc": credit_card_data.cvc,

        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.payota.net/api/public/v1/manage/init_partners",
            headers=headers,
            json=payload
        )

        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)

        response = response.json()

        if "status" not in response:
            raise UnprocessableEntity(message="Что-то пошло не так")

        return response["status"]


    def raw_booking_hotel(
            self,
            partner_order_id: str,
            payment_type: str,
            amount: str,
            currency_code: str,
            client: ClientBookingData,
            init_uuid: Optional[str] = None,
            pay_uuid: Optional[str] = None,

    ):
        payload = {
            "language": "ru",
            "pay_uuid": str(uuid.uuid4()),
            "partner": {"partner_order_id": partner_order_id},
            "payment_type": {
                "type": payment_type,
                "amount": amount,
                "currency_code": currency_code,
                "init_uuid": init_uuid,
                "pay_uuid": pay_uuid
            },
            "upsell_data": [],
            "return_path": "http://109.73.199.21/api/v1/success",
            "rooms": [
                {
                "guests": [
                    {
                        "first_name": "Фы",
                        "last_name": "Фы",
                    }
                ]
                }
            ],
            "user": {
                "email": "s.pashov@axas.ru",
                "phone": "79024066769"
            },
            "supplier_data": client.dict()

        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/booking/finish/",
            headers=headers,
            json=payload
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response.json()

    def raw_check_booking(
            self,
            partner_order_id: str
    ):
        payload = {
            "partner_order_id": partner_order_id,

        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/booking/finish/status/",
            headers=headers,
            json=payload
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)
        if "data" not in response:
            logging.info("ETG response: %s", response)
        print(response.json())

        return response.json()


    def raw_search_by_hid(
        self,
        checkin: int,
        checkout: int,
        guests: Optional[List[RoomGuests]]
    ):
        checkin_date = str(from_unix_timestamp(checkin).date())
        checkout_date = str(from_unix_timestamp(checkout).date())
        payload = {
            "checkin": checkin_date,
            "checkout": checkout_date,
            "ids": ['test_hotel_do_not_book'],
            # "hids": [6291619],
        }
        if guests:
            payload["guests"] = [
                guest.dict(exclude_unset=True) for guest in guests
            ]
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/search/serp/hotels/",
            headers=headers,
            json=payload
        ).json()

        return response

    def raw_get_test_hotel(
            self,
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
            "id": "test_hotel_do_not_book"
        }
        if guests:
            payload["guests"] = [
                guest.dict(exclude_unset=True) for guest in gest_list
            ]
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/search/hp/",
            headers=headers,
            json=payload
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)
        if "data" not in response:
            logging.info("ETG response: %s", response)
        print(response.json())

        return response.json()


    def raw_get_bookings(
            self,
    ):
        payload = {
          "ordering": {
            "ordering_type": "desc",
            "ordering_by": "created_at"
          },
          "pagination": {
            "page_size": "10",
            "page_number": "1"
          }
        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/info/",
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response


    def cancel_booking(
            self,
            partner_order_id: str
    ):
        payload = {
          "partner_order_id": partner_order_id
        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/cancel/",
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        if response["status"] == "ok":
            return response["status"]
        else:
            raise UnprocessableEntity(message="Что-то пошло не так, попробуйте снова")



    def secure_check(
            self,
            url: str,
            data: dict,
            method: str = 'post'
    ):
        payload = data
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": f"Basic {self.encoded_credentials}"
        # }
        response = requests.post(
            url,
            # headers=headers,
            json=payload,
            allow_redirects=True,
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)
        # if "data" not in response:
        #     logging.info("ETG response: %s", response)
        # print(response.json())
        #
        # return response.json()


    def prebooking(
            self,
            book_hash: str
    ):
        payload = {
            "hash": book_hash
        }
        logging.info("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/prebook/",
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        first_rate =response["data"]["hotels"][0]["rates"][0]

        match_hash = first_rate["match_hash"]
        new_book_hash = first_rate["book_hash"]
        free_cancellation_before = first_rate["payment_options"]["payment_types"][0]["cancellation_penalties"]["free_cancellation_before"]
        if free_cancellation_before:
            free_cancellation_before = from_unix_timestamp(to_unix_timestamp(
                datetime.strptime(free_cancellation_before, "%Y-%m-%dT%H:%M:%S")))
        pre_book_data = PreCreatedBooking(
            hotel_hid=response["data"]["hotels"][0]["hid"],
            room_name=first_rate["room_name"],
            hotel_name=first_rate["legal_info"]["hotel"]["name"],
            free_cancellation_before=free_cancellation_before,
            has_free_cancellation=True if free_cancellation_before else False
        )
        return new_book_hash, match_hash, pre_book_data


    def create_booking(
            self,
            db: Session,
            book_hash: str,
            match_hash: str,
            checkin: int,
            checkout: int,
            user_id: int
    ):
        new_book_hash, verify_hash, pre_book_data = self.prebooking(book_hash=book_hash)
        if match_hash != verify_hash:
            raise UnprocessableEntity(message="Что-то пошло не так, обновите страницу")
        payload = {
            "partner_order_id": str(uuid.uuid4()),
            "book_hash": new_book_hash,
            "language": "ru",
            "user_ip": "109.73.199.21"
        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/booking/form/",
            headers=headers,
            json=payload
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)


        resp = response.json()
        if "data" not in resp:
            raise UnprocessableEntity(message="Что-то пошло не так, попробуйте снова")
        pay_data = resp["data"]["payment_types"][0]
        creating_data = CreatedBooking(
            price=int(float(pay_data["amount"]) * 100),
            currency=pay_data["currency_code"],
            etg_pay_type=pay_data["type"],
            item_id=resp["data"]["item_id"],
            order_id=resp["data"]["order_id"],
            partner_order_id=resp["data"]["partner_order_id"],
            checkin=from_unix_timestamp(checkin).date(),
            checkout=from_unix_timestamp(checkout).date(),
            user_id=user_id,
            is_need_credit_card_data=pay_data["is_need_credit_card_data"],
            is_need_cvc=pay_data["is_need_cvc"]
        )
        new_hotel_booking = crud.hotel_booking.create(db=db, obj_in=creating_data, **pre_book_data.dict())


        return CreatingBooking(
                is_need_credit_card_data=new_hotel_booking.is_need_credit_card_data,
                booking_id=new_hotel_booking.id,
                is_payment_now=True if new_hotel_booking.etg_pay_type == "now" else False
            )


    def booking_hotel(
            self,
            db: Session,
            booking_id: int,
            user_data: BookingUserData,

    ):
        booking = crud.hotel_booking.get_by_id(db=db, id=booking_id)
        if booking is None:
            raise UnfoundEntity(
                message="Бронирование не найдено"
            )
        pay_uuid = str(uuid.uuid4())
        init_uuid = str(uuid.uuid4())
        if booking.is_need_credit_card_data:
            status_credit_card_token = self.create_credit_card_token(
                object_id=str(booking.item_id),
                user_first_name=user_data.first_name,
                user_last_name=user_data.last_name,
                pay_uuid=pay_uuid,
                init_uuid=init_uuid,
                credit_card_data=user_data.card_data,
                is_cvc_required=booking.is_need_cvc
            )

            if status_credit_card_token != "ok":
                raise UnprocessableEntity(message="Что-то пошло не так, попробуйте снова")

            booking.pay_uuid = pay_uuid
            booking.init_uuid = init_uuid
            db.commit()
            db.refresh(booking)

        payload = {
            "language": "ru",
            "partner": {"partner_order_id": booking.partner_order_id},
            "payment_type": {
                "type": booking.etg_pay_type,
                "amount": str(booking.price / 100),
                "currency_code": booking.currency,
                "init_uuid": init_uuid,
                "pay_uuid": pay_uuid
            },
            "upsell_data": [],
            "return_path": "http://109.73.199.21/api/v1/success",
            "rooms": [
                {
                "guests": [
                    {
                        "first_name": user_data.first_name,
                        "last_name": user_data.last_name,
                    }
                ]
                }
            ],
            "user": {
                "email": user_data.email,
                "phone": user_data.phone
            },
            "supplier_data": {
                "first_name_original": user_data.first_name,
                "last_name_original": user_data.last_name,
                "phone": user_data.phone,
                "email": user_data.email
            }

        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/booking/finish/",
            headers=headers,
            json=payload
        )
        logging.info("ETG response status code: %s", response.status_code)
        print("ETG response status code: %s", response.status_code)
        logging.info("Response headers: %s", response.headers)
        print("Response headers: %s", response.headers)
        logging.info("ETG response: %s", response.content)
        print("ETG response: %s", response.content)

        resp = response.json()
        if resp["status"] == "ok" or resp["error"] in ("unknown", "timeout"):
            check = self.raw_check_booking(partner_order_id=booking.partner_order_id)
            if check["status"] == "processing":
                print('****   STATUS processing   ****')
                booking.status = HotelBookingStatus.PROCESSING
                db.add(booking)
                db.commit()
                db.refresh(booking)

                stop_event = threading.Event()
                thread = threading.Thread(
                    target=self._check_status_in_thread,
                    args=(booking.partner_order_id, stop_event, db),
                    daemon=True
                )
                thread.start()

            return CreatingBooking(
                is_need_credit_card_data=booking.is_need_credit_card_data,
                booking_id=booking.id,
                is_payment_now=True if booking.etg_pay_type == "now" else False
            )
        else:
            raise UnprocessableEntity(message="Что-то пошло не так")


    def raw_get_test_hotel_dump(
            self,
    ):
        payload = {
            "id": "test_hotel_do_not_book",
            "language": "ru",
        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/info/",
            headers=headers,
            json=payload
        ).json()
        if "data" not in response:
            logging.info("ETG response: %s", response)

        return response


    def get_bookings_info(
            self,
            db: Session,
            bookings: List[HotelBooking],
            page: int
    ):
        if not bookings:
            return []
        order_ids =[row[0] for row in
            (
            db.query(HotelBooking.order_id)
            .filter(
                HotelBooking.user_id == bookings[0].user.id,
                HotelBooking.status != HotelBookingStatus.NEW,
            )
            .order_by(HotelBooking.created.desc())
            .all()
        )
        ]

        unique_hotel_hids = [row[0] for row in
            (
            db.query(HotelBooking.hotel_hid)
            .filter(
                HotelBooking.user_id == user.id,
                HotelBooking.status != HotelBookingStatus.NEW,
            )
            .distinct()
            .all()
        )]

        payload = {
            "ordering": {
                "ordering_type": "desc",
                "ordering_by": "created_at"
            },
            "pagination": {
                "page_size": "30",
                "page_number": page
            },
            "search": {
                "order_ids": order_ids
            },
            "language": "ru",
        }
        logging.info("Payload for search: %s", payload)
        print("Payload for search: %s", payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}"
        }
        response = requests.post(
            "https://api.worldota.net/api/b2b/v3/hotel/order/info/",
            headers=headers,
            json=payload
        ).json()

        actual_statuses = {}  # order_id: status
        for order in response["data"]["orders"]:
            actual_statuses[order["order_id"]] = order["status"]
            # booking = bookings_dict[order["order_id"]]
            # print(booking.status)
            # if order["status"] not in ("noshow", "failed", "error") and order["status"] != booking.status:
            #     booking.status = order["status"]
            #     db.add(booking)
            #     db.commit()
            #     db.refresh(booking)

        # Получение фото из дампа
        hids_images = {}
        try:
            with open(DUMP_PATH, "r", encoding="utf-8") as file:
                for line in file:
                    hotel_data = json.loads(line.strip())
                    if hotel_data.get("hid") in unique_hotel_hids:
                        image_url = hotel_data.get("images")[0].replace('{size}', PICT_SIZE)
                        hids_images[hotel_data.get("hid")] = image_url
        except Exception as e:
            print(e)

        booking_infos = []
        for booking in bookings:
            if (booking.order_id in actual_statuses
                    and (actual_statuses[booking.order_id] not in ("noshow", "failed", "error")
                         and actual_statuses[booking.order_id] != booking.status)):
                booking.status = actual_statuses[booking.order_id]
                db.add(booking)
                db.commit()
                db.refresh(booking)
            booking_info = GettingBooking(
                id=booking.id,
                created=to_unix_timestamp(booking.created),
                checkin=to_unix_timestamp(booking.checkin),
                checkout=to_unix_timestamp(booking.checkout),
                hotel_name=booking.hotel_name,
                room_name=booking.room_name,
                price=booking.price,
                status=booking.status,
                hotel_image=hids_images[booking.hotel_hid],
                has_free_cancellation=booking.has_free_cancellation,
                free_cancellation_before=to_unix_timestamp(booking.free_cancellation_before)
            )
            booking_infos.append(booking_info)

        return booking_infos


        # bookings_dict = {}  # { order_id: HotelBooking }
        # order_ids = []
        # hids_images = {}
        # for booking in bookings:
        #     order_ids.append(booking.order_id)
        #     hids_images[booking.hotel_hid] = None
        #     bookings_dict[booking.order_id] = booking_info = GettingBooking(
        #             id=booking.id,
        #             created=to_unix_timestamp(booking.created),
        #             checkin=to_unix_timestamp(booking.checkin),
        #             checkout=to_unix_timestamp(booking.checkout),
        #             hotel_name=booking.hotel_name,
        #             room_name=booking.room_name,
        #             price=booking.price,
        #             status=booking.status,
        #             hotel_image=None,
        #             has_free_cancellation=booking.has_free_cancellation,
        #             free_cancellation_before=to_unix_timestamp(booking.free_cancellation_before)
        #         )
        #
        #
        #
        # payload = {
        #     "ordering": {
        #         "ordering_type": "desc",
        #         "ordering_by": "created_at"
        #     },
        #     "pagination": {
        #         "page_size": "30",
        #         "page_number": page
        #     },
        #     "search": {
        #         "order_ids": order_ids
        #     },
        #     "language": "ru",
        # }
        # logging.info("Payload for search: %s", payload)
        # print("Payload for search: %s", payload)
        #
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": f"Basic {self.encoded_credentials}"
        # }
        # response = requests.post(
        #     "https://api.worldota.net/api/b2b/v3/hotel/order/info/",
        #     headers=headers,
        #     json=payload
        # ).json()
        #
        # booking_infos = []
        # for order in response["data"]["orders"]:
        #     booking = bookings_dict[order["order_id"]]
        #     print(booking.status)
        #     if order["status"] not in ("noshow", "failed", "error") and order["status"] != booking.status:
        #         booking.status = order["status"]
        #         db.add(booking)
        #         db.commit()
        #         db.refresh(booking)
        #
        #     if booking.status != HotelBookingStatus.NEW:
        #         booking_info = GettingBooking(
        #             id=booking.id,
        #             created=to_unix_timestamp(booking.created),
        #             checkin=to_unix_timestamp(booking.checkin),
        #             checkout=to_unix_timestamp(booking.checkout),
        #             hotel_name=booking.hotel_name,
        #             room_name=booking.room_name,
        #             price=booking.price,
        #             status=booking.status,
        #             hotel_image=hids_images[booking.hotel_hid],
        #             has_free_cancellation=booking.has_free_cancellation,
        #             free_cancellation_before=to_unix_timestamp(booking.free_cancellation_before)
        #         )
        #         booking_infos.append(booking_info)
        #
        # return booking_infos

    def get_booking(
            self,
            db: Session,
            booking: HotelBooking,
    ):
        # bookings_dict = {}  # { order_id: HotelBooking }
        # order_ids = []
        # hids_images = {}
        # for booking in bookings:
        #     order_ids.append(booking.order_id)
        #     hids_images[booking.hotel_hid] = None
        #     bookings_dict[booking.order_id] = booking

        # Получение фото из дампа
        hotel_images = []
        room_images = []
        try:
            with open(DUMP_PATH, "r", encoding="utf-8") as file:
                for line in file:
                    hotel_data = json.loads(line.strip())
                    if hotel_data.get("hid") == booking.hotel_hid:
                        hotel_images = [
                            image_url.replace('{size}', PICT_SIZE) for image_url in hotel_data.get("images")
                        ]
                    for room in hotel_data.get("room_groups"):
                        if room["name"] == booking.room_name:
                            room_images = [
                                image_url.replace('{size}', PICT_SIZE) for image_url in room.get("images")
                            ]
        except Exception as e:
            print(e)

        booking_info = GettingDetailBooking(
            id=booking.id,
            created=to_unix_timestamp(booking.created),
            checkin=to_unix_timestamp(booking.checkin),
            checkout=to_unix_timestamp(booking.checkout),
            hotel_name=booking.hotel_name,
            room_name=booking.room_name,
            price=booking.price,
            status=booking.status,
            hotel_image=hotel_images,
            has_free_cancellation=booking.has_free_cancellation,
            free_cancellation_before=to_unix_timestamp(booking.free_cancellation_before),
            room_images=room_images
        )
        return booking_info


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

