"""订单查询 API 测试。"""

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.api.main import app
from ecom_agent.commerce.database import get_session
from ecom_agent.commerce.order_models import (
    OrderItemRecord,
    OrderRecord,
)
from ecom_agent.commerce.order_repository import OrderRepository


@contextmanager
def create_test_client() -> Iterator[TestClient]:
    """创建连接到独立测试数据库的 API 客户端。"""

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        repository = OrderRepository(session)

        repository.add(
            OrderRecord(
                order_id="order-001",
                user_id="user-001",
                status="shipped",
                total_amount=Decimal("2298.00"),
            ),
            [
                OrderItemRecord(
                    order_id="order-001",
                    product_id="phone-001",
                    product_name="学习手机",
                    quantity=1,
                    unit_price=Decimal("1999.00"),
                ),
                OrderItemRecord(
                    order_id="order-001",
                    product_id="keyboard-001",
                    product_name="机械键盘",
                    quantity=1,
                    unit_price=Decimal("299.00"),
                ),
            ],
        )

        repository.add(
            OrderRecord(
                order_id="order-002",
                user_id="user-002",
                status="paid",
                total_amount=Decimal("4299.00"),
            ),
            [
                OrderItemRecord(
                    order_id="order-002",
                    product_id="laptop-001",
                    product_name="轻薄办公本",
                    quantity=1,
                    unit_price=Decimal("4299.00"),
                ),
            ],
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


def test_get_order_for_owner() -> None:
    """订单所有者应该能够查询自己的订单。"""

    with create_test_client() as client:
        response = client.get(
            "/orders/order-001",
            params={"user_id": "user-001"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["order_id"] == "order-001"
    assert data["user_id"] == "user-001"
    assert data["status"] == "shipped"
    assert Decimal(data["total_amount"]) == Decimal("2298.00")

    assert len(data["items"]) == 2
    assert data["items"][0]["product_id"] == "phone-001"
    assert data["items"][0]["product_name"] == "学习手机"
    assert data["items"][0]["quantity"] == 1


def test_other_user_cannot_get_order() -> None:
    """用户查询其他用户订单时应该返回 404。"""

    with create_test_client() as client:
        response = client.get(
            "/orders/order-001",
            params={"user_id": "user-002"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}


def test_missing_order_returns_404() -> None:
    """查询不存在的订单时应该返回 404。"""

    with create_test_client() as client:
        response = client.get(
            "/orders/order-not-found",
            params={"user_id": "user-001"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}


def test_order_query_requires_user_id() -> None:
    """订单查询必须提供用户 ID。"""

    with create_test_client() as client:
        response = client.get("/orders/order-001")

    assert response.status_code == 422
