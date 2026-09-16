from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

SectionType = Literal[
    "banner",
    "testimonials",
    "counters",
    "custom_html",
    "announcement_bar",
    "header",
    "products",
    "text",
    "categories",
    "image",
    "footer",
    "section_heading",
    "decant_callout",
    "manifesto",
    "hero_product",
    "gallery",
]


class PageSectionResponse(BaseModel):
    id: int
    page: str
    type: str
    position: int
    is_active: bool
    content: dict
    key: str | None
    is_builtin: bool

    model_config = {"from_attributes": True}


class PageSectionHistoryResponse(BaseModel):
    id: int
    section_id: int | None
    page: str
    key: str | None
    type: str
    content: dict
    is_active: bool
    position: int
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PageSectionCreate(BaseModel):
    page: str = Field(min_length=1)
    type: SectionType
    content: dict
    is_active: bool = True


class PageSectionUpdate(BaseModel):
    content: dict | None = None
    is_active: bool | None = None


class PageSectionMove(BaseModel):
    direction: Literal["up", "down"]


def _reject_markup(value: str, field_name: str) -> str:
    """Los mensajes de la barra de anuncios se pintan con textContent en el
    frontend (nunca innerHTML), pero igual se rechaza `<`/`>` acá: si el admin
    escribe algo que parece HTML, es más útil avisarle que dejarlo pensar que
    se va a interpretar como marcado cuando en realidad va a salir tal cual.
    """
    if "<" in value or ">" in value:
        raise ValueError(f"{field_name} no puede contener HTML")
    return value


def _validate_link(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("/"):
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("El enlace debe ser una ruta interna (que empiece con /) o una URL http/https completa")
    return value


class AnnouncementMessage(BaseModel):
    text: str = Field(min_length=1, max_length=90)
    highlight: str | None = Field(default=None, max_length=90)
    link_url: str | None = None
    is_active: bool = True
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_validator("text")
    @classmethod
    def _text_no_markup(cls, v: str) -> str:
        return _reject_markup(v.strip(), "El texto")

    @field_validator("highlight")
    @classmethod
    def _highlight_no_markup(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        return _reject_markup(v, "El destacado")

    @field_validator("link_url")
    @classmethod
    def _link_valid(cls, v: str | None) -> str | None:
        return _validate_link(v)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "AnnouncementMessage":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
        return self


class AnnouncementBarContent(BaseModel):
    messages: list[AnnouncementMessage] = Field(min_length=1)
    position: Literal["top", "inline"] = "inline"
    rotation_interval: int = Field(default=5, ge=3, le=10)
    transition: Literal["fade", "slide"] = "fade"
    closable: bool = False
    variant: Literal["onyx", "paper", "gold-soft"] = "onyx"


def validate_announcement_bar_content(content: dict) -> dict:
    """Valida y normaliza el content de una sección announcement_bar. Se
    guarda con mode="json" (fechas como texto ISO) porque `content` es una
    columna JSON: un `datetime` de Python no es serializable ahí directo.
    Lanza pydantic.ValidationError si algo no cumple — la ruta la traduce a
    un 422 con el detalle de cada campo.
    """
    return AnnouncementBarContent(**content).model_dump(mode="json")
