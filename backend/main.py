import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text

load_dotenv()

logging.basicConfig(level=logging.INFO)


def _get_client_ip(request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


app = FastAPI(title="JG Parfums API")

limiter = Limiter(key_func=_get_client_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_URL", "http://localhost:8000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Los routers se importan después de crear `limiter`: varios hacen
# `from main import limiter` para decorar sus endpoints con @limiter.limit(...).
from routes import auth, categories, orders, page_sections, payments, products, settings, stats  # noqa: E402

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(stats.router)
app.include_router(page_sections.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"service": "JG Parfums API", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"database": "ok"}
    except Exception:
        logging.getLogger("jg_parfums.db").exception("db-check falló")
        return {"database": "error"}
    finally:
        db.close()
