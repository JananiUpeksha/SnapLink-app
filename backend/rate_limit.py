from fastapi import Request, HTTPException
from redis_client import redis_client

RATE_LIMIT = 5          # max requests
WINDOW_SECONDS = 60     # per this many seconds

def check_rate_limit(request: Request):
    ip = request.client.host
    key = f"ratelimit:{ip}"

    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, WINDOW_SECONDS)

    if current > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
