from typing import Literal

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    image_url: str | None
    eyebrow: str | None
    display_name: str | None
    overlay_darkness: int
    text_position: str
    blur: int
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    image_url: str | None = None
    eyebrow: str | None = Field(default=None, max_length=60)
    display_name: str | None = None
    overlay_darkness: int = Field(default=40, ge=0, le=100)
    text_position: Literal["left", "center", "right"] = "left"
    blur: int = Field(default=0, ge=0, le=20)
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, min_length=1)
    image_url: str | None = None
    eyebrow: str | None = Field(default=None, max_length=60)
    display_name: str | None = None
    overlay_darkness: int | None = Field(default=None, ge=0, le=100)
    text_position: Literal["left", "center", "right"] | None = None
    blur: int | None = Field(default=None, ge=0, le=20)
    is_active: bool | None = None


class CategoryMove(BaseModel):
    direction: Literal["up", "down"]
