from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from schemas.category import CategoryResponse


class ProductImageResponse(BaseModel):
    id: int
    url: str
    alt_text: str
    position: int

    model_config = {"from_attributes": True}


class ProductImageCreate(BaseModel):
    url: str
    alt_text: str
    position: int = 0


class ProductVariantResponse(BaseModel):
    id: int
    size_ml: int
    price: int
    final_price: int  # con el descuento del producto ya aplicado
    stock: int
    is_active: bool
    image_url: str | None = None

    model_config = {"from_attributes": True}


class ProductVariantCreate(BaseModel):
    size_ml: int = Field(gt=0)
    price: int = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    image_url: str | None = None


class ProductVariantUpdate(BaseModel):
    price: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    image_url: str | None = None


class ProductDetailSectionResponse(BaseModel):
    id: int
    title: str
    body: str
    position: int

    model_config = {"from_attributes": True}


class ProductDetailSectionCreate(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class ProductDetailSectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    body: str | None = Field(default=None, min_length=1)


class ProductDetailSectionMove(BaseModel):
    direction: Literal["up", "down"]


class ProductMediaItemResponse(BaseModel):
    id: int
    url: str
    alt_text: str
    title: str | None = None
    subtitle: str | None = None
    text_position: str
    text_position_vertical: str
    overlay_opacity: int
    blur: int
    height_px: int
    width_pct: int
    position: int

    model_config = {"from_attributes": True}


class ProductMediaItemCreate(BaseModel):
    url: str = Field(min_length=1)
    alt_text: str = ""
    title: str | None = None
    subtitle: str | None = None
    text_position: Literal["left", "center", "right"] = "left"
    text_position_vertical: Literal["top", "center", "bottom"] = "bottom"
    overlay_opacity: int = Field(default=0, ge=0, le=100)
    blur: int = Field(default=0, ge=0, le=20)
    height_px: int = Field(default=480, gt=0, le=1200)
    width_pct: int = Field(default=100, ge=20, le=100)


class ProductMediaItemUpdate(BaseModel):
    url: str | None = Field(default=None, min_length=1)
    alt_text: str | None = None
    title: str | None = None
    subtitle: str | None = None
    text_position: Literal["left", "center", "right"] | None = None
    text_position_vertical: Literal["top", "center", "bottom"] | None = None
    overlay_opacity: int | None = Field(default=None, ge=0, le=100)
    blur: int | None = Field(default=None, ge=0, le=20)
    height_px: int | None = Field(default=None, gt=0, le=1200)
    width_pct: int | None = Field(default=None, ge=20, le=100)


class ProductMediaItemMove(BaseModel):
    direction: Literal["up", "down"]


class ProductNoteResponse(BaseModel):
    id: int
    name: str
    color: str
    position: int

    model_config = {"from_attributes": True}


class ProductNoteCreate(BaseModel):
    name: str = Field(min_length=1)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class ProductNoteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ProductNoteMove(BaseModel):
    direction: Literal["up", "down"]


class ProductBase(BaseModel):
    name: str = Field(min_length=1)
    house: str | None = None
    description: str = Field(min_length=1)
    concentration: str | None = None
    size_ml: int = Field(gt=0)
    price: int = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    discount_percent: int = Field(ge=0, le=99, default=0)
    is_active: bool = True
    is_featured: bool = False


class ProductCreate(ProductBase):
    slug: str = Field(min_length=1)
    # Una, dos o más — nunca obligatorio, un producto puede quedar sin
    # clase todavía (igual que antes con category_id=None).
    category_ids: list[int] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: str | None = None
    house: str | None = None
    description: str | None = None
    concentration: str | None = None
    size_ml: int | None = Field(default=None, gt=0)
    price: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    discount_percent: int | None = Field(default=None, ge=0, le=99)
    is_active: bool | None = None
    is_featured: bool | None = None
    # None = no tocar las clases actuales; [] = dejarlo sin ninguna.
    category_ids: list[int] | None = None


class ProductResponse(ProductBase):
    id: int
    slug: str
    final_price: int  # `price` con `discount_percent` ya aplicado
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageResponse] = []
    variants: list[ProductVariantResponse] = []
    notes: list[ProductNoteResponse] = []
    detail_sections: list[ProductDetailSectionResponse] = []
    media_items: list[ProductMediaItemResponse] = []
    categories: list[CategoryResponse] = []

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
