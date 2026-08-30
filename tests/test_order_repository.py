"""订单仓储测试。"""

from decimal import Decimal

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.commerce.order_models import (
    OrderItemRecord,
    OrderRecord,
)
from ecom_agent.commerce.order_repository import OrderRepository
from ecom_agent.commerce.seed import seed_orders


def create_test_session() -> Session:
    """创建一个独立的内存数据库会话。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def add_demo_order(
    session: Session,
    order_id: str = "order-001",
    user_id: str = "user-001",
) -> OrderRecord:
    """添加一个测试订单。"""

    repository = OrderRepository(session)
    order = OrderRecord(
        order_id=order_id,
        user_id=user_id,
        status="shipped",
        total_amount=Decimal("2298.00"),
    )
    items = [
        OrderItemRecord(
            order_id=order_id,
            product_id="phone-001",
            product_name="学习手机",
            quantity=1,
            unit_price=Decimal("1999.00"),
        ),
        OrderItemRecord(
            order_id=order_id,
            product_id="keyboard-001",
            product_name="机械键盘",
            quantity=1,
            unit_price=Decimal("299.00"),
        ),
    ]

    return repository.add(order, items)


def test_add_and_get_order_for_user() -> None:
    """用户应该能够查询自己的订单。"""

    with create_test_session() as session:
        repository = OrderRepository(session)
        add_demo_order(session)

        result = repository.get_by_id_for_user(
            order_id="order-001",
            user_id="user-001",
        )
        items = repository.list_items("order-001")

    assert result is not None
    assert result.order_id == "order-001"
    assert result.user_id == "user-001"
    assert result.status == "shipped"
    assert result.total_amount == Decimal("2298.00")

    assert len(items) == 2
    assert items[0].product_id == "phone-001"
    assert items[0].quantity == 1
    assert items[1].product_id == "keyboard-001"


def test_order_is_hidden_from_other_user() -> None:
    """用户不应该查询到其他用户的订单。"""

    with create_test_session() as session:
        repository = OrderRepository(session)
        add_demo_order(session)

        result = repository.get_by_id_for_user(
            order_id="order-001",
            user_id="user-002",
        )

    assert result is None


def test_missing_order_returns_none() -> None:
    """查询不存在的订单时应该返回 None。"""

    with create_test_session() as session:
        repository = OrderRepository(session)

        result = repository.get_by_id_for_user(
            order_id="order-not-found",
            user_id="user-001",
        )

    assert result is None


def test_seed_orders_inserts_demo_data_once() -> None:
    """演示订单只能被初始化一次。"""

    with create_test_session() as session:
        repository = OrderRepository(session)

        first_count = seed_orders(session)
        second_count = seed_orders(session)
        orders = repository.list_all()

        first_items = repository.list_items("order-001")
        second_items = repository.list_items("order-002")

    assert first_count == 2
    assert second_count == 0
    assert len(orders) == 2
    assert len(first_items) == 2
    assert len(second_items) == 1