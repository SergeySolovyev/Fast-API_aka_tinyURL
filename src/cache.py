import json
from typing import Any

from redis import asyncio as aioredis

from src.config import REDIS_URL


redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_cache(key: str) -> Any | None:
    if redis_client is None:
        return None

    value = await redis_client.get(key)
    if value is None:
        return None

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def set_cache(key: str, value: Any, expire: int) -> None:
    if redis_client is None:
        return

    await redis_client.set(key, json.dumps(value, default=str), ex=expire)


async def delete_cache(*keys: str) -> None:
    if redis_client is None or not keys:
        return

    await redis_client.delete(*keys)