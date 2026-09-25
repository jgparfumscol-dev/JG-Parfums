"""FRONTEND_URL admite varios orígenes separados por coma (CORS necesita todos:
el dominio propio y el de Cloudflare Pages), pero un enlace que se manda por
correo o a una pasarela necesita UNO. El primero de la lista es el canónico."""

import os

_DEFAULT = "http://localhost:8000"


def frontend_origins() -> list[str]:
    raw = os.environ.get("FRONTEND_URL", _DEFAULT)
    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    return origins or [_DEFAULT]


def frontend_base_url() -> str:
    return frontend_origins()[0]
