from datetime import datetime

from pydantic import BaseModel, Field


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


class ProductBase(BaseModel):
    name: str = Field(min_length=1)
    house: str | None = None
    description: str = Field(min_length=1)
    olfactory_family: str | None = None
    notes_top: str | None = None
    notes_heart: str | None = None
    notes_base: str | None = None
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
    olfactory_family: str | None = None
    notes_top: str | None = None
    notes_heart: str | None = None
    notes_base: str | None = None
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

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
