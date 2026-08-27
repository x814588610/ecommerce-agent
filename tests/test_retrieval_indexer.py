"""测试商品索引编排逻辑。"""

from decimal import Decimal

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.documents import ProductDocument
from ecom_agent.retrieval.indexer import index_products


class FakeVectorStore:
    """记录收到的商品文档的测试向量存储。"""

    def __init__(self) -> None:
        self.documents: list[ProductDocument] = []

    def upsert_documents(
        self,
        documents: list[ProductDocument],
    ) -> int:
        """保存收到的文档并返回数量。"""

        self.documents = list(documents)
        return len(self.documents)


def create_session() -> Session:
    """创建一个内存数据库会话。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    return Session(engine)


def create_product() -> ProductRecord:
    """创建一个测试商品。"""

    return ProductRecord(
        product_id="phone-001",
        name="学习手机",
        category="手机",
        brand="星河",
        description="适合学生学习和日常使用。",
        price=Decimal("1999.00"),
        stock=20,
        tags_json='["学生", "学习"]',
    )


def test_index_products_builds_and_writes_documents() -> None:
    """索引器应该读取商品并交给向量存储。"""

    with create_session() as session:
        ProductRepository(session).add(create_product())
        vector_store = FakeVectorStore()

        count = index_products(session, vector_store)

    assert count == 1
    assert len(vector_store.documents) == 1
    assert vector_store.documents[0].product_id == "phone-001"
    assert "商品名称：学习手机" in vector_store.documents[0].text


def test_index_products_returns_zero_for_empty_database() -> None:
    """数据库为空时不应写入任何文档。"""

    with create_session() as session:
        vector_store = FakeVectorStore()

        count = index_products(session, vector_store)

    assert count == 0
    assert vector_store.documents == []