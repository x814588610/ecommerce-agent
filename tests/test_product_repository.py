"""Tests for the product repository."""

from decimal import Decimal

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.commerce.seed import seed_products


def create_test_session() -> Session:
    """Create a fresh in-memory database session for testing."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_add_and_get_product() -> None:
    """A saved product should be retrievable by its ID."""

    with create_test_session() as session:
        repository = ProductRepository(session)
        product = ProductRecord(
            product_id="phone-001",
            name="学习手机",
            category="手机",
            brand="Example",
            description="适合学生学习使用",
            price=Decimal("1999.00"),
            stock=10,
            tags_json='["学生", "学习"]',
        )

        repository.add(product)
        result = repository.get_by_id("phone-001")

        assert result is not None
        assert result.name == "学习手机"
        assert result.price == Decimal("1999.00")


def test_search_filters_out_of_stock_and_price() -> None:
    """Search should filter out-of-stock and expensive products."""

    with create_test_session() as session:
        repository = ProductRepository(session)
        repository.add(
            ProductRecord(
                product_id="phone-001",
                name="学习手机",
                category="手机",
                brand="Example",
                description="适合学生学习使用",
                price=Decimal("1999.00"),
                stock=10,
            )
        )
        repository.add(
            ProductRecord(
                product_id="phone-002",
                name="昂贵手机",
                category="手机",
                brand="Example",
                description="高端手机",
                price=Decimal("5999.00"),
                stock=10,
            )
        )
        repository.add(
            ProductRecord(
                product_id="phone-003",
                name="缺货手机",
                category="手机",
                brand="Example",
                description="暂时缺货",
                price=Decimal("999.00"),
                stock=0,
            )
        )

        results = repository.search(
            category="手机",
            max_price=Decimal("3000.00"),
        )

        assert [product.product_id for product in results] == ["phone-001"]


def test_search_by_name_or_description() -> None:
    """Search should match the product name or description."""

    with create_test_session() as session:
        repository = ProductRepository(session)
        repository.add(
            ProductRecord(
                product_id="keyboard-001",
                name="机械键盘",
                category="电脑配件",
                description="适合编程和办公",
                price=Decimal("299.00"),
                stock=5,
            )
        )

        results = repository.search(query="编程")

        assert len(results) == 1
        assert results[0].product_id == "keyboard-001"


def test_seed_products_inserts_demo_data_once() -> None:
    """Demo products should be inserted once without duplication."""

    with create_test_session() as session:
        repository = ProductRepository(session)

        first_count = seed_products(session)
        second_count = seed_products(session)
        products = repository.list_all()

        assert first_count == 5
        assert second_count == 0
        assert len(products) == 5