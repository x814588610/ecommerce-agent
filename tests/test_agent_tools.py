"""Tests for LangChain commerce tools."""

import json
from decimal import Decimal

import pytest
from langchain_core.tools import StructuredTool
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.agent.tools import (
    ProductSearchToolInput,
    create_inventory_tool,
    create_product_detail_tool,
    create_product_search_tool,
)
from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository


def create_test_session() -> Session:
    """Create an in-memory database session with demo products."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    session = Session(engine)
    repository = ProductRepository(session)
    repository.add(
        ProductRecord(
            product_id="phone-001",
            name="学习手机",
            category="手机",
            brand="星河",
            description="适合学生学习使用",
            price=Decimal("1999.00"),
            stock=10,
        )
    )
    repository.add(
        ProductRecord(
            product_id="phone-002",
            name="缺货手机",
            category="手机",
            brand="星河",
            description="暂时缺货的手机",
            price=Decimal("999.00"),
            stock=0,
        )
    )
    repository.add(
        ProductRecord(
            product_id="laptop-001",
            name="轻薄办公本",
            category="电脑",
            brand="远山",
            description="适合办公和编程",
            price=Decimal("4299.00"),
            stock=5,
        )
    )
    return session


def test_create_product_search_tool() -> None:
    """The factory should return a configured LangChain tool."""

    with create_test_session() as session:
        search_tool = create_product_search_tool(session)

    assert isinstance(search_tool, StructuredTool)
    assert search_tool.name == "search_products"
    assert "query" in search_tool.args
    assert "max_price" in search_tool.args


def test_tool_invoke_excludes_out_of_stock_products() -> None:
    """The tool should exclude out-of-stock products by default."""

    with create_test_session() as session:
        search_tool = create_product_search_tool(session)
        raw_result = search_tool.invoke({"query": "手机"})

    products = json.loads(raw_result)

    assert [product["product_id"] for product in products] == ["phone-001"]


def test_tool_invoke_applies_category_and_price_filters() -> None:
    """The tool should apply category and maximum price filters."""

    with create_test_session() as session:
        search_tool = create_product_search_tool(session)
        raw_result = search_tool.invoke(
            {
                "category": "电脑",
                "max_price": "5000.00",
            }
        )

    products = json.loads(raw_result)

    assert len(products) == 1
    assert products[0]["product_id"] == "laptop-001"
    assert products[0]["price"] == "4299.00"


def test_tool_input_rejects_negative_price() -> None:
    """The tool input model should reject a negative maximum price."""

    with pytest.raises(ValidationError):
        ProductSearchToolInput(max_price=Decimal("-1.00"))


def test_product_detail_tool_returns_product() -> None:
    """The detail tool should return complete product information."""

    with create_test_session() as session:
        detail_tool = create_product_detail_tool(session)
        raw_result = detail_tool.invoke({"product_id": "phone-001"})

    product = json.loads(raw_result)

    assert product["product_id"] == "phone-001"
    assert product["name"] == "学习手机"
    assert product["price"] == "1999.00"
    assert product["stock"] == 10


def test_product_detail_tool_returns_not_found() -> None:
    """The detail tool should report a missing product."""

    with create_test_session() as session:
        detail_tool = create_product_detail_tool(session)
        raw_result = detail_tool.invoke({"product_id": "missing-001"})

    result = json.loads(raw_result)

    assert result == {
        "error": "product_not_found",
        "product_id": "missing-001",
    }


def test_inventory_tool_reports_available_product() -> None:
    """The inventory tool should report an available product."""

    with create_test_session() as session:
        inventory_tool = create_inventory_tool(session)
        raw_result = inventory_tool.invoke({"product_id": "phone-001"})

    inventory = json.loads(raw_result)

    assert inventory["product_id"] == "phone-001"
    assert inventory["stock"] == 10
    assert inventory["in_stock"] is True


def test_inventory_tool_reports_out_of_stock_product() -> None:
    """The inventory tool should report an out-of-stock product."""

    with create_test_session() as session:
        inventory_tool = create_inventory_tool(session)
        raw_result = inventory_tool.invoke({"product_id": "phone-002"})

    inventory = json.loads(raw_result)

    assert inventory["product_id"] == "phone-002"
    assert inventory["stock"] == 0
    assert inventory["in_stock"] is False