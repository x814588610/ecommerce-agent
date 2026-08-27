"""测试商品语义搜索服务。"""

from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.search import search_products_semantically
from ecom_agent.retrieval.vector_store import ProductSearchResult


class FakeVectorStore:
    """返回固定搜索结果并记录调用参数。"""

    def __init__(
        self,
        results: list[ProductSearchResult],
    ) -> None:
        self.results = results
        self.calls: list[tuple[str, int, bool]] = []

    def search(
        self,
        query: str,
        limit: int = 5,
        only_in_stock: bool = True,
    ) -> list[ProductSearchResult]:
        """模拟向量搜索并记录收到的参数。"""

        self.calls.append((query, limit, only_in_stock))
        return self.results


def create_session() -> Session:
    """创建一个隔离的内存数据库会话。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def create_product(
    product_id: str,
    name: str,
    stock: int = 10,
) -> ProductRecord:
    """创建一条测试商品记录。"""

    return ProductRecord(
        product_id=product_id,
        name=name,
        category="数码产品",
        brand="星河",
        description=f"{name}的商品描述",
        price=Decimal("1999.00"),
        stock=stock,
        tags_json='["学习", "数码"]',
    )


def create_vector_result(
    product_id: str,
    score: float,
    stock: int = 10,
) -> ProductSearchResult:
    """创建一条模拟的 Qdrant 搜索结果。"""

    return ProductSearchResult(
        product_id=product_id,
        score=score,
        payload={
            "product_id": product_id,
            "stock": stock,
        },
    )


def test_search_returns_products_in_vector_order() -> None:
    """结果应该保持向量相似度返回的顺序。"""

    with create_session() as session:
        repository = ProductRepository(session)
        repository.add(create_product("phone-001", "学习手机"))
        repository.add(create_product("laptop-001", "编程电脑"))

        vector_store = FakeVectorStore(
            [
                create_vector_result("laptop-001", 0.95),
                create_vector_result("phone-001", 0.82),
            ]
        )

        results = search_products_semantically(
            session=session,
            vector_store=vector_store,
            query="适合学习和编程的设备",
            limit=2,
        )

        assert [result.product.product_id for result in results] == [
            "laptop-001",
            "phone-001",
        ]
        assert [result.score for result in results] == [0.95, 0.82]
        assert all(result.source == "qdrant" for result in results)
        assert vector_store.calls == [
            ("适合学习和编程的设备", 2, True)
        ]


def test_search_skips_products_missing_from_database() -> None:
    """SQLite 中已经不存在的商品应该被跳过。"""

    with create_session() as session:
        ProductRepository(session).add(
            create_product("phone-001", "学习手机")
        )
        vector_store = FakeVectorStore(
            [
                create_vector_result("deleted-001", 0.99),
                create_vector_result("phone-001", 0.80),
            ]
        )

        results = search_products_semantically(
            session=session,
            vector_store=vector_store,
            query="学习手机",
        )

        assert [result.product.product_id for result in results] == [
            "phone-001"
        ]


def test_search_uses_latest_database_stock() -> None:
    """库存��断应该以 SQLite 的最新数据为准。"""

    with create_session() as session:
        ProductRepository(session).add(
            create_product(
                "phone-001",
                "学习手机",
                stock=0,
            )
        )
        vector_store = FakeVectorStore(
            [
                create_vector_result(
                    "phone-001",
                    0.95,
                    stock=20,
                )
            ]
        )

        in_stock_results = search_products_semantically(
            session=session,
            vector_store=vector_store,
            query="学习手机",
        )
        all_results = search_products_semantically(
            session=session,
            vector_store=vector_store,
            query="学习手机",
            only_in_stock=False,
        )

        assert in_stock_results == []
        assert len(all_results) == 1
        assert all_results[0].product.stock == 0


def test_search_rejects_non_positive_limit() -> None:
    """搜索数量必须大于零。"""

    vector_store = FakeVectorStore([])

    with create_session() as session, pytest.raises(ValueError, match="greater than zero"):
         search_products_semantically(
             session=session,
             vector_store=vector_store,
             query="学习手机",
             limit=0,
         )

    assert vector_store.calls == []