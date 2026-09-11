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
]


class PageSectionResponse(BaseModel):
    id: int
    page: str
    type: str
    position: int
    is_active: bool
    content: dict

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
