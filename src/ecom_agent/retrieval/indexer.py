"""将 SQLite 商品同步到向量数据库。"""

from sqlmodel import Session

from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.documents import build_product_document
from ecom_agent.retrieval.vector_store import ProductVectorStore


def index_products(
    session: Session,
    vector_store: ProductVectorStore,
) -> int:
    """读取全部商品并写入商品向量库。"""

    repository = ProductRepository(session)
    products = repository.list_all()
    documents = [
        build_product_document(product)
        for product in products
    ]

    return vector_store.upsert_documents(documents)