"""LangChain tools for commerce operations."""

import json
from decimal import Decimal

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field
from sqlmodel import Session

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository


class ProductSearchToolInput(BaseModel):
    """Input parameters accepted by the product search tool."""

    query: str = Field(
        default="",
        description="Keywords in the product name or description.",
    )
    category: str | None = Field(
        default=None,
        description="Product category, such as phone or computer.",
    )
    brand: str | None = Field(
        default=None,
        description="Product brand.",
    )
    max_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Maximum acceptable price.",
    )
    only_in_stock: bool = Field(
        default=True,
        description="Whether to exclude out-of-stock products.",
    )

class ProductIdToolInput(BaseModel):
    """Input parameters accepted by product ID tools."""

    product_id: str = Field(
        min_length=1,
        description="The unique product ID.",
    )


def _serialize_product(record: ProductRecord) -> dict[str, object]:
    """Convert a database record into JSON-compatible data."""

    return {
        "product_id": record.product_id,
        "name": record.name,
        "category": record.category,
        "brand": record.brand,
        "description": record.description,
        "price": str(record.price),
        "stock": record.stock,
        "tags": json.loads(record.tags_json),
    }

def _product_not_found(product_id: str) -> str:
    """Return a machine-readable missing-product result."""

    return json.dumps(
        {
            "error": "product_not_found",
            "product_id": product_id,
        },
        ensure_ascii=False,
    )

def create_product_search_tool(session: Session) -> StructuredTool:
    """Create a LangChain tool backed by a database session."""

    repository = ProductRepository(session)

    @tool(args_schema=ProductSearchToolInput)
    def search_products(
        query: str = "",
        category: str | None = None,
        brand: str | None = None,
        max_price: Decimal | None = None,
        only_in_stock: bool = True,
    ) -> str:
        """Search products by keywords, category, brand, price, and stock."""

        records = repository.search(
            query=query,
            category=category,
            brand=brand,
            max_price=max_price,
            only_in_stock=only_in_stock,
        )
        products = [_serialize_product(record) for record in records]

        return json.dumps(products, ensure_ascii=False)

    return search_products


def create_product_detail_tool(session: Session) -> StructuredTool:
    """Create a LangChain tool for retrieving product details."""

    repository = ProductRepository(session)

    @tool(args_schema=ProductIdToolInput)
    def get_product_detail(product_id: str) -> str:
        """Return complete details for one product."""

        record = repository.get_by_id(product_id)

        if record is None:
            return _product_not_found(product_id)

        return json.dumps(
            _serialize_product(record),
            ensure_ascii=False,
        )

    return get_product_detail


def create_inventory_tool(session: Session) -> StructuredTool:
    """Create a LangChain tool for checking product inventory."""

    repository = ProductRepository(session)

    @tool(args_schema=ProductIdToolInput)
    def check_inventory(product_id: str) -> str:
        """Return the current stock status for one product."""

        record = repository.get_by_id(product_id)

        if record is None:
            return _product_not_found(product_id)

        inventory = {
            "product_id": record.product_id,
            "name": record.name,
            "stock": record.stock,
            "in_stock": record.stock > 0,
        }
        return json.dumps(inventory, ensure_ascii=False)

    return check_inventory