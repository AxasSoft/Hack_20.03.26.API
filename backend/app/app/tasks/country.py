import time

import requests
from fastapi_utils.tasks import repeat_every

from app.api import deps
from app.main import app
from app.models import User

DELTA_SECONDS = 60*60*6


@app.on_event("startup")
@repeat_every(seconds=DELTA_SECONDS, wait_first=True)
def check_country() -> None:
    print('checking countries...')
    db = next(deps.get_db())

    user_map = {}

    for user in db.query(User).filter(User.tel != None, User.country == None):

        print(f'checking {user.tel}')

        url = f"https://api3.greensms.ru/hlr/send?to={user.tel}&user=AllPortugal&pass=dcyhzv7P"

        payload = {}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            data = response.json()
            print(data)
            request_id = data['request_id']
            if request_id is None:
                raise ValueError()
        except:
            continue

        user_map[user.tel] = [request_id, None]

    print('wake down')
    time.sleep(300)
    print('wake up')
    for tel, [request_id, country] in user_map.items():
        stop = False
        while not stop:
            url = f"https://api3.greensms.ru/hlr/status?&user=AllPortugal&pass=dcyhzv7P&id={request_id}&to={tel}"

            payload = {}
            headers = {}

            response = requests.request("POST", url, headers=headers, data=payload)

            try:
                data = response.json()
                if data.get('status') != 'Status not ready':
                    stop = True
                else:
                    time.sleep(90)
                    continue
                print(data)
                country = data['cn']
                if country is None:
                    raise ValueError()
            except:
                break
        if country is not None:
            user_map[tel][1] = country

    print('saving data')
    for tel, [request_id, country] in user_map.items():
        user = db.query(User).filter(User.tel == tel).first()
        if user is not None:
            user.country = country
            db.add(user)

    db.commit()
    print('countries checked')