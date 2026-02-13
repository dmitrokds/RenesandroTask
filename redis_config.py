import config
import redis.asyncio

r = redis.asyncio.Redis(
    host="redis",
    decode_responses=True,
)
