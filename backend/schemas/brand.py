from typing import Literal

from pydantic import BaseModel, Field, field_validator

from schemas.page_section import _validate_link


class BrandResponse(BaseModel):
    id: int
    name: str
    logo_url: str
    link_url: str | None
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class BrandCreate(BaseModel):
    name: str = Field(min_length=1)
    logo_url: str = Field(min_length=1)
    link_url: str | None = None
    is_active: bool = True

    @field_validator("link_url")
    @classmethod
    def _link_valid(cls, v: str | None) -> str | None:
        return _validate_link(v)


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    logo_url: str | None = Field(default=None, min_length=1)
    link_url: str | None = None
    is_active: bool | None = None

    @field_validator("link_url")
    @classmethod
    def _link_valid(cls, v: str | None) -> str | None:
        return _validate_link(v)


class BrandMove(BaseModel):
    direction: Literal["up", "down"]
