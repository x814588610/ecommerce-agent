"""商品语义搜索 API 测试。"""

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
from ecom_agent.retrieval.factory import get_product_vector_store
from ecom_agent.retrieval.vector_store import ProductSearchResult


class FakeVectorStore:
    """模拟商品向量存储。"""

    def __init__(self, results: list[ProductSearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int, bool]] = []
        self.filter_calls: list[
            tuple[str | None, str | None, Decimal | None]
        ] = []

    def search(
        self,
        query: str,
        limit: int = 5,
        only_in_stock: bool = True,
        category: str | None = None,
        brand: str | None = None,
        max_price: Decimal | None = None,
    ) -> list[ProductSearchResult]:
        """记录搜索参数并返回模拟结果。"""

        self.calls.append((query, limit, only_in_stock))
        self.filter_calls.append((category, brand, max_price))
        return self.results


def create_product(
    product_id: str,
    name: str,
    stock: int,
    price: Decimal = Decimal("1999.00"),
) -> ProductRecord:
    """创建测试商品。"""

    return ProductRecord(
        product_id=product_id,
        name=name,
        category="数码产品",
        brand="星河",
        description=f"{name}的商品描述",
        price=price,
        stock=stock,
        tags_json='["学习", "数码"]',
    )


@contextmanager
def create_test_client(
    vector_store: FakeVectorStore,
) -> Iterator[TestClient]:
    """创建使用隔离数据库和模拟向量存储的测试客户端。"""

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        repository = ProductRepository(session)
        repository.add(
            create_product(
                "phone-001",
                "学习手机",
                stock=10,
            )
        )
        repository.add(
            create_product(
                "phone-002",
                "缺货手机",
                stock=0,
            )
        )
        repository.add(
            create_product(
                "laptop-001",
                "昂贵电脑",
                stock=5,
                price=Decimal("3999.00"),
            )
        )

    def override_get_session() -> Iterator[Session]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_product_vector_store] = lambda: vector_store

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def create_vector_result(
    product_id: str,
    score: float,
) -> ProductSearchResult:
    """创建模拟的向量搜索结果。"""

    return ProductSearchResult(
        product_id=product_id,
        score=score,
        payload={
            "product_id": product_id,
        },
    )


def test_semantic_search_returns_product_and_score() -> None:
    """语义搜索应该返回商品详情、相似度和来源。"""

    vector_store = FakeVectorStore(
        [
            create_vector_result("phone-001", 0.93),
        ]
    )

    with create_test_client(vector_store) as client:
        response = client.get(
            "/products/semantic",
            params={
                "query": "适合学生学习的手机",
                "limit": 3,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "product": {
                    "product_id": "phone-001",
                    "name": "学习手机",
                    "category": "数码产品",
                    "brand": "星河",
                    "description": "学习手机的商品描述",
                    "price": "1999.00",
                    "stock": 10,
                    "tags": ["学习", "数码"],
                },
                "score": 0.93,
                "source": "qdrant",
            }
        ],
        "total": 1,
    }
    assert vector_store.calls == [
        ("适合学生学习的手机", 3, True),
    ]


def test_semantic_search_can_include_out_of_stock_products() -> None:
    """关闭库存过滤后应该允许返回缺货商品。"""

    vector_store = FakeVectorStore(
        [
            create_vector_result("phone-002", 0.88),
        ]
    )

    with create_test_client(vector_store) as client:
        response = client.get(
            "/products/semantic",
            params={
                "query": "备用手机",
                "only_in_stock": "false",
            },
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["product"]["product_id"] == "phone-002"
    assert response.json()["items"][0]["product"]["stock"] == 0
    assert vector_store.calls == [
        ("备用手机", 5, False),
    ]


def test_semantic_search_validates_query_and_limit() -> None:
    """语义搜索应该拒绝空查询和过大的返回数量。"""

    vector_store = FakeVectorStore([])

    with create_test_client(vector_store) as client:
        empty_query_response = client.get(
            "/products/semantic",
            params={"query": ""},
        )
        large_limit_response = client.get(
            "/products/semantic",
            params={
                "query": "手机",
                "limit": 21,
            },
        )

    assert empty_query_response.status_code == 422
    assert large_limit_response.status_code == 422
    assert vector_store.calls == []


def test_semantic_search_applies_structured_filters() -> None:
    """语义搜索应该执行类别、品牌和最高价格过滤。"""

    vector_store = FakeVectorStore(
        [
            create_vector_result("phone-001", 0.93),
            create_vector_result("phone-002", 0.88),
            create_vector_result("laptop-001", 0.86),
        ]
    )

    with create_test_client(vector_store) as client:
        response = client.get(
            "/products/semantic",
            params={
                "query": "适合学习的设备",
                "category": "数码产品",
                "brand": "星河",
                "max_price": "2000",
                "only_in_stock": "false",
            },
        )

    assert response.status_code == 200

    product_ids = [
        item["product"]["product_id"]
        for item in response.json()["items"]
    ]

    assert product_ids == ["phone-001", "phone-002"]
    assert vector_store.filter_calls == [
        (
            "数码产品",
            "星河",
            Decimal("2000"),
        )
    ]
