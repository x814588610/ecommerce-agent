"""Tests for retrieval document preparation."""

from decimal import Decimal

import pytest

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.retrieval.documents import build_product_document


def create_product(tags_json: str) -> ProductRecord:
    """Create one product for testing."""

    return ProductRecord(
        product_id="phone-001",
        name="学习手机",
        category="手机",
        brand="星河",
        description="适合学生学习和日常使用的入门手机。",
        price=Decimal("1999.00"),
        stock=20,
        tags_json=tags_json,
    )


def test_build_product_document() -> None:
    """The product should be converted into text and payload."""

    document = build_product_document(
        create_product('["学生", "学习", "入门"]')
    )

    assert document.product_id == "phone-001"
    assert "商品名称：学习手机" in document.text
    assert "商品类别：手机" in document.text
    assert "商品描述：适合学生学习和日常使用的入门手机。" in document.text
    assert "商品标签：学生, 学习, 入门" in document.text

    assert document.payload["name"] == "学习手机"
    assert document.payload["brand"] == "星河"
    assert document.payload["price"] == "1999.00"
    assert document.payload["stock"] == 20
    assert document.payload["tags"] == ["学生", "学习", "入门"]


def test_build_product_document_rejects_invalid_json() -> None:
    """Invalid tag JSON should raise a clear error."""

    with pytest.raises(ValueError, match="Invalid tags JSON"):
        build_product_document(create_product("not-json"))


def test_build_product_document_rejects_non_list_tags() -> None:
    """Tags JSON must contain a list."""

    with pytest.raises(ValueError, match="must be a JSON list"):
        build_product_document(create_product('{"tag": "学习"}'))