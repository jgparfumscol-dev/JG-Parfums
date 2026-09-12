from typing import Literal

from pydantic import BaseModel, Field

FontPairing = Literal["classic", "warm", "elegant", "minimal", "editorial"]
HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"


class SiteSettingsResponse(BaseModel):
    store_name: str
    accent_color: str
    font_pairing: str
    whatsapp_number: str | None
    instagram_url: str | None
    tiktok_url: str | None
    contact_email: str | None
    contact_phone: str | None
    shipping_cost: int

    model_config = {"from_attributes": True}


class SiteSettingsUpdate(BaseModel):
    store_name: str | None = Field(default=None, min_length=1)
    accent_color: str | None = Field(default=None, pattern=HEX_COLOR_PATTERN)
    font_pairing: FontPairing | None = None
    whatsapp_number: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    shipping_cost: int | None = Field(default=None, ge=0)
