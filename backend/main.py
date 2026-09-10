from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import URL, Click
from schemas import ShortenRequest, ShortenResponse, StatsResponse
from redis_client import redis_client
from utils import generate_short_code
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
from rate_limit import check_rate_limit
from fastapi import Request

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SnapLink API")

Instrumentator().instrument(app).expose(app)

redirect_cache_hits = Counter("snaplink_redirect_cache_hits_total", "Redirects served from Redis cache")
redirect_cache_misses = Counter("snaplink_redirect_cache_misses_total", "Redirects requiring DB lookup")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request)
    code = generate_short_code()
    while db.query(URL).filter(URL.short_code == code).first():
        code = generate_short_code()

    entry = URL(short_code=code, long_url=str(payload.long_url))
    db.add(entry)
    db.commit()
    db.refresh(entry)

    redis_client.setex(f"url:{code}", 3600, entry.long_url)

    return ShortenResponse(short_code=code, short_url=f"/{code}")

@app.get("/{code}")
def redirect_url(code: str, db: Session = Depends(get_db)):
    cached_url = redis_client.get(f"url:{code}")

    if cached_url:
        redirect_cache_hits.inc()
        redis_client.incr(f"clicks:{code}")
        return RedirectResponse(url=cached_url)

    redirect_cache_misses.inc()
    entry = db.query(URL).filter(URL.short_code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Short code not found")

    redis_client.setex(f"url:{code}", 3600, entry.long_url)
    redis_client.incr(f"clicks:{code}")

    return RedirectResponse(url=entry.long_url)

@app.get("/stats/{code}", response_model=StatsResponse)
def get_stats(code: str, db: Session = Depends(get_db)):
    entry = db.query(URL).filter(URL.short_code == code).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Short code not found")

    pending = int(redis_client.get(f"clicks:{code}") or 0)

    flushed = db.query(Click).filter(Click.short_code == code).first()
    flushed_count = flushed.click_count if flushed else 0

    return StatsResponse(
        short_code=entry.short_code,
        long_url=entry.long_url,
        click_count=flushed_count + pending,
        created_at=entry.created_at,
    )
