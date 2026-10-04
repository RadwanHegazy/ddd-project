import json, os, redis
from typing import Optional, Any


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))


class RedisCache:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        json_data = json.dumps(value)
        self.client.setex(name=key, value=json_data, time=ttl_seconds)

    def delete(self, key: str) -> None:
        self.client.delete(key)

    def delete_pattern(self, pattern: str) -> None:
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)