from decimal import Decimal

from sqlmodel import Field, SQLModel


class ProductRecord(SQLModel, table=True):
    """A product stored in the local SQLite database."""

    __tablename__ = "products"

    product_id: str = Field(
        primary_key=True,
        max_length=50,
    )
    name: str = Field(
        index=True,
        max_length=200,
    )
    category: str = Field(
        index=True,
        max_length=100,
    )
    brand: str = Field(
        default="",
        index=True,
        max_length=100,
    )
    description: str = ""
    price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        max_digits=12,
    )
    stock: int = Field(
        default=0,
        ge=0,
    )
    tags_json: str = "[]"