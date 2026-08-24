"""Product query API routes."""

import json
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ecom_agent.commerce.database import get_session
from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.schemas.product import Product, ProductSearchResponse

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


def _to_product(record: ProductRecord) -> Product:
    """Convert a database record into an API response model."""

    return Product(
        product_id=record.product_id,
        name=record.name,
        category=record.category,
        brand=record.brand,
        description=record.description,
        price=record.price,
        stock=record.stock,
        tags=json.loads(record.tags_json),
    )


@router.get("", response_model=ProductSearchResponse)
def search_products(
    session: Annotated[Session, Depends(get_session)],
    query: str = "",
    category: str | None = None,
    brand: str | None = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    only_in_stock: bool = True,
) -> ProductSearchResponse:
    """Search products using optional filters."""

    repository = ProductRepository(session)
    records = repository.search(
        query=query,
        category=category,
        brand=brand,
        max_price=max_price,
        only_in_stock=only_in_stock,
    )
    products = [_to_product(record) for record in records]

    return ProductSearchResponse(
        items=products,
        total=len(products),
    )


@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> Product:
    """Return one product by its ID."""

    repository = ProductRepository(session)
    record = repository.get_by_id(product_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return _to_product(record)