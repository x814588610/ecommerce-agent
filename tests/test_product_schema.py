"""Tests for product Pydantic schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from ecom_agent.schemas.product import Product, ProductSearchRequest


def test_product_accepts_valid_data() -> None:
    """A valid product should be created successfully."""

    product = Product(
        product_id="phone-001",
        name="学习手机",
        category="手机",
        brand="星河",
        description="适合学生学习使用",
        price=Decimal("1999.00"),
        stock=10,
        tags=["学生", "学习"],
    )

    assert product.product_id == "phone-001"
    assert product.price == Decimal("1999.00")
    assert product.stock == 10
    assert product.tags == ["学生", "学习"]


def test_product_rejects_negative_price() -> None:
    """A product price cannot be negative."""

    with pytest.raises(ValidationError):
        Product(
            product_id="phone-001",
            name="学习手机",
            category="手机",
            price=Decimal("-1.00"),
            stock=10,
        )


def test_product_rejects_negative_stock() -> None:
    """A product stock value cannot be negative."""

    with pytest.raises(ValidationError):
        Product(
            product_id="phone-001",
            name="学习手机",
            category="手机",
            price=Decimal("1999.00"),
            stock=-1,
        )


def test_product_rejects_empty_product_id() -> None:
    """A product ID cannot be empty."""

    with pytest.raises(ValidationError):
        Product(
            product_id="",
            name="学习手机",
            category="手机",
            price=Decimal("1999.00"),
            stock=10,
        )


def test_search_request_has_expected_defaults() -> None:
    """A search request should use the expected default filters."""

    request = ProductSearchRequest(query="手机")

    assert request.query == "手机"
    assert request.category is None
    assert request.brand is None
    assert request.max_price is None
    assert request.only_in_stock is True