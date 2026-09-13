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
    stock: int
    is_active: bool

    model_config = {"from_attributes": True}


class ProductVariantCreate(BaseModel):
    size_ml: int = Field(gt=0)
    price: int = Field(gt=0)
    stock: int = Field(ge=0, default=0)


class ProductVariantUpdate(BaseModel):
    price: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


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
    category_id: int | None = None
    concentration: str | None = None
    size_ml: int = Field(gt=0)
    price: int = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    slug: str = Field(min_length=1)


class ProductUpdate(BaseModel):
    name: str | None = None
    house: str | None = None
    description: str | None = None
    category_id: int | None = None
    concentration: str | None = None
    size_ml: int | None = Field(default=None, gt=0)
    price: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageResponse] = []
    variants: list[ProductVariantResponse] = []
    notes: list[ProductNoteResponse] = []
    category: CategoryResponse | None = None

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
