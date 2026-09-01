import os
import time
import redis
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://snaplink:snaplink@localhost:5432/snaplink")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
FLUSH_INTERVAL = int(os.getenv("FLUSH_INTERVAL", "10"))

engine = create_engine(DATABASE_URL)
r = redis.from_url(REDIS_URL, decode_responses=True)

def flush_clicks():
    keys = r.keys("clicks:*")
    if not keys:
        return

    with engine.begin() as conn:
        for key in keys:
            short_code = key.split(":", 1)[1]
            count = int(r.get(key) or 0)
            if count == 0:
                continue

            result = conn.execute(
                text("SELECT click_count FROM clicks WHERE short_code = :code"),
                {"code": short_code}
            ).fetchone()

            if result:
                conn.execute(
                    text("UPDATE clicks SET click_count = click_count + :count, last_updated = now() WHERE short_code = :code"),
                    {"count": count, "code": short_code}
                )
            else:
                conn.execute(
                    text("INSERT INTO clicks (short_code, click_count, last_updated) VALUES (:code, :count, now())"),
                    {"code": short_code, "count": count}
                )

            r.delete(key)
            print(f"Flushed {count} clicks for {short_code}")

if __name__ == "__main__":
    print("SnapLink worker started")
    while True:
        try:
            flush_clicks()
        except Exception as e:
            print(f"Worker error: {e}")
        time.sleep(FLUSH_INTERVAL)
