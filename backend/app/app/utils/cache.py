import json
from typing import Any, Type, Optional

from pydantic import BaseModel
from redis import Redis

class Cache:
    def __init__(self, redis: Redis, response_schema: Optional[Type[BaseModel]], ttl):
        self.response_schema = response_schema
        self.redis = redis
        self.ttl = ttl

    @staticmethod
    def format_key(key_tuple: tuple) -> bytes:
        return (":".join(str(item) for item in key_tuple)).encode()

    @staticmethod
    def encode_body(body: Any) -> bytes:
        return json.dumps(body).encode()

    @staticmethod
    def decode_body(body: bytes) -> Any:
        return json.loads(body.decode())

    def get_raw(self, key_tuple: tuple) -> Any:
        key = self.format_key(key_tuple)
        data = self.redis.get(key)
        if data is None:
            return None

        caching_data = self.decode_body(data)
        if self.response_schema is None:
            return caching_data

        return self.decode_body(data)

    def set_raw(self, key_tuple: tuple, body: Any, ttl=None):
        key = self.format_key(key_tuple)
        data = self.encode_body(body)
        self.redis.set(key, data, ex=self.ttl if ttl is None else ttl)

    def get(self, key_tuple: tuple):
        data = self.get_raw(key_tuple)
        if data is None:
            return None

        return self.response_schema(**data)

    def set(self, key_tuple: tuple, body: BaseModel, ttl=None):
        self.set_raw(
            key_tuple, body.dict() if body is not None else None, ttl
        )

    def delete(self, key_tuple: tuple):
        key = self.format_key(key_tuple)
        self.redis.delete(key)

    def delete_by_prefix(self, prefix: str):
        for key in self.redis.keys(prefix + "*"):
            self.redis.delete(key)

    def behind_cache(self, key_tuple, func, ttl=None):
        "data.data: from db -> GettingAuction, from cache -> dict."

        data = self.get(key_tuple)
        if data is not None:
            print("from cache =>")
            return data, True

        print("from db =>")
        data = func()
        self.set(key_tuple, data, ttl)
        return data, False
    
    async def behind_cache_asyc(self, key_tuple, func, ttl=None):
        "data.data: from db -> GettingAuction, from cache -> dict."

        data = self.get(key_tuple)
        if data is not None:
            print("from cache =>")
            return data, True

        print("from db =>")
        data = await func()
        self.set(key_tuple, data, ttl)
        return data, False


    def get_keys(self, prefix: str):
        return self.redis.keys(prefix)