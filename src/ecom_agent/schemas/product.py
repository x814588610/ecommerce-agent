"""Product request and response schemas."""

from decimal import Decimal

from pydantic import BaseModel, Field


class Product(BaseModel):
    """A product displayed by the commerce system."""
    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    brand: str = ""
    description: str = ""
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    tags: list[str] = Field(default_factory=list)


class ProductSearchRequest(BaseModel):
    """Filters accepted by the product search endpoint."""

    query: str = Field(min_length=1)
    category: str | None = None
    brand: str | None = None
    max_price: Decimal | None = Field(default=None, ge=0)
    only_in_stock: bool = True


class ProductSearchResponse(BaseModel):
    """A product search result page."""

    items: list[Product]
    total: int = Field(ge=0)
