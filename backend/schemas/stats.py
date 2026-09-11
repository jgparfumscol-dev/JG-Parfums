from pydantic import BaseModel, Field


class PageViewCreate(BaseModel):
    path: str = Field(min_length=1, max_length=300)
    referrer: str | None = Field(default=None, max_length=300)


class DayCount(BaseModel):
    date: str
    count: int


class PathCount(BaseModel):
    path: str
    count: int


class ProductCount(BaseModel):
    name: str
    quantity: int


class StatsSummary(BaseModel):
    views_7d: int
    views_30d: int
    views_by_day: list[DayCount]
    top_pages: list[PathCount]
    total_orders: int
    total_revenue: int
    orders_by_status: dict[str, int]
    top_products: list[ProductCount]
