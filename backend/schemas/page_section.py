from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SectionType = Literal[
    "banner",
    "testimonials",
    "counters",
    "custom_html",
    "announcement",
    "header",
    "products",
    "text",
    "categories",
    "image",
    "footer",
    "section_heading",
    "decant_callout",
    "manifesto",
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
