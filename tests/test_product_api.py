"""Tests for the product query API."""

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.api.main import app
from ecom_agent.commerce.database import get_session
from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository


@contextmanager
def create_test_client() -> Iterator[TestClient]:
    """Create an API client connected to an isolated test database."""

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        repository = ProductRepository(session)
        repository.add(
            ProductRecord(
                product_id="phone-001",
                name="学习手机",
                category="手机",
                brand="星河",
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
                price=Decimal("4299.00"),
                stock=5,
            )
        )

    def override_get_session() -> Iterator[Session]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)

    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_list_products_excludes_out_of_stock() -> None:
    """The default product list should exclude unavailable products."""

    with create_test_client() as client:
        response = client.get("/products")

    assert response.status_code == 200
    data = response.json()
    product_ids = {item["product_id"] for item in data["items"]}

    assert data["total"] == 2
    assert product_ids == {"phone-001", "laptop-001"}


def test_filter_products_by_category_and_price() -> None:
    """Product filters should enforce category and maximum price."""

    with create_test_client() as client:
        response = client.get(
            "/products",
            params={
                "category": "手机",
                "max_price": "3000.00",
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["product_id"] == "phone-001"


def test_get_product_by_id() -> None:
    """An existing product should be returned by its ID."""

    with create_test_client() as client:
        response = client.get("/products/phone-001")

    assert response.status_code == 200
    assert response.json()["name"] == "学习手机"


def test_get_missing_product_returns_404() -> None:
    """A missing product should return HTTP 404."""

    with create_test_client() as client:
        response = client.get("/products/not-found")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


def test_negative_max_price_returns_422() -> None:
    """A negative maximum price should fail input validation."""

    with create_test_client() as client:
        response = client.get(
            "/products",
            params={"max_price": "-1"},
        )

    assert response.status_code == 422