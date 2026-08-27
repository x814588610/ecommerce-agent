"""测试 Agent 的商品语义搜索工具。"""

import json
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.agent.tools import (
    SemanticProductSearchToolInput,
    create_semantic_product_search_tool,
)
from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.vector_store import ProductSearchResult


class FakeVectorStore:
    """模拟商品向量存储。"""

    def __init__(self, results: list[ProductSearchResult]) -> None:
        self.results = results
        self.calls: list[
            tuple[str, int, bool, str | None, str | None, Decimal | None]
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
        """记录搜索参数并返回固定结果。"""

        self.calls.append(
            (
                query,
                limit,
                only_in_stock,
                category,
                brand,
                max_price,
            )
        )
        return self.results


def create_session() -> Session:
    """创建包含测试商品的内存数据库会话。"""

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
            description="适合学生学习和日常使用。",
            price=Decimal("1999.00"),
            stock=10,
            tags_json='["学生", "学习"]',
        )
    )
    repository.add(
        ProductRecord(
            product_id="phone-002",
            name="缺货手机",
            category="手机",
            brand="星河",
            description="暂时缺货的备用手机。",
            price=Decimal("999.00"),
            stock=0,
            tags_json='["备用"]',
        )
    )

    return session


def create_vector_result(
    product_id: str,
    score: float,
) -> ProductSearchResult:
    """创建模拟的向量搜索结果。"""

    return ProductSearchResult(
        product_id=product_id,
        score=score,
        payload={"product_id": product_id},
    )


def test_semantic_tool_returns_product_score_and_source() -> None:
    """语义工具应该返回商品、相似度和来源。"""

    vector_store = FakeVectorStore(
        [
            create_vector_result("phone-001", 0.93),
            create_vector_result("phone-002", 0.88),
        ]
    )

    with create_session() as session:
        semantic_tool = create_semantic_product_search_tool(
            session,
            vector_store,
        )
        raw_result = semantic_tool.invoke(
            {
                "query": "适合学生学习的手机",
                "limit": 3,
            }
        )

    result = json.loads(raw_result)

    assert result["total"] == 1
    assert result["items"][0] == {
        "product": {
            "product_id": "phone-001",
            "name": "学习手机",
            "category": "手机",
            "brand": "星河",
            "description": "适合学生学习和日常使用。",
            "price": "1999.00",
            "stock": 10,
            "tags": ["学生", "学习"],
        },
        "score": 0.93,
        "source": "qdrant",
    }
    assert vector_store.calls == [
        (
            "适合学生学习的手机",
            3,
            True,
            None,
            None,
            None,
        ),
    ]


def test_semantic_tool_can_include_out_of_stock_products() -> None:
    """关闭库存过滤后应该返回缺货商品。"""

    vector_store = FakeVectorStore(
        [
            create_vector_result("phone-002", 0.88),
        ]
    )

    with create_session() as session:
        semantic_tool = create_semantic_product_search_tool(
            session,
            vector_store,
        )
        raw_result = semantic_tool.invoke(
            {
                "query": "备用手机",
                "only_in_stock": False,
            }
        )

    result = json.loads(raw_result)

    assert result["total"] == 1
    assert result["items"][0]["product"]["product_id"] == "phone-002"
    assert result["items"][0]["product"]["stock"] == 0
    assert vector_store.calls == [
        (
            "备用手机",
            5,
            False,
            None,
            None,
            None,
        ),
    ]

def test_semantic_tool_input_validates_query_and_limit() -> None:
    """语义工具输入应该校验查询文本和返回数量。"""

    with pytest.raises(ValidationError):
        SemanticProductSearchToolInput(query="")

    with pytest.raises(ValidationError):
        SemanticProductSearchToolInput(
            query="手机",
            limit=21,
        )


def test_semantic_tool_applies_structured_filters() -> None:
    """语义工具应该传递并执行类别、品牌和最高价格过滤。"""

    vector_store = FakeVectorStore(
        [
            create_vector_result("phone-001", 0.93),
            create_vector_result("phone-002", 0.88),
        ]
    )

    with create_session() as session:
        semantic_tool = create_semantic_product_search_tool(
            session,
            vector_store,
        )
        raw_result = semantic_tool.invoke(
            {
                "query": "手机",
                "category": "手机",
                "brand": "星河",
                "max_price": "1500",
                "only_in_stock": False,
            }
        )

    result = json.loads(raw_result)

    assert result["total"] == 1
    assert result["items"][0]["product"]["product_id"] == "phone-002"
    assert result["items"][0]["product"]["price"] == "999.00"
    assert vector_store.calls == [
        (
            "手机",
            5,
            False,
            "手机",
            "星河",
            Decimal("1500"),
        ),
    ]