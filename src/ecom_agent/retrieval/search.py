"""组合向量检索结果和数据库商品记录。"""

from dataclasses import dataclass
from decimal import Decimal

from sqlmodel import Session

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.vector_store import ProductVectorStore


@dataclass(frozen=True, slots=True)
class SemanticProductResult:
    """包含完整商品信息的语义搜索结果。"""

    product: ProductRecord
    score: float
    source: str = "qdrant"


def search_products_semantically(
    session: Session,
    vector_store: ProductVectorStore,
    query: str,
    limit: int = 5,
    only_in_stock: bool = True,
    category: str | None = None,
    brand: str | None = None,
    max_price: Decimal | None = None,
) -> list[SemanticProductResult]:
    """使用语义相似度搜索商品并读取最新数据库记录。"""

    if limit <= 0:
        raise ValueError("Search limit must be greater than zero.")

    if max_price is not None and max_price < 0:
        raise ValueError("Maximum price must not be negative.")

    if category is None and brand is None and max_price is None:
        vector_results = vector_store.search(
            query=query,
            limit=limit,
            only_in_stock=only_in_stock,
        )
    else:
        vector_results = vector_store.search(
            query=query,
            limit=limit,
            only_in_stock=only_in_stock,
            category=category,
            brand=brand,
            max_price=max_price,
        )

    repository = ProductRepository(session)
    results: list[SemanticProductResult] = []

    for vector_result in vector_results:
        product = repository.get_by_id(vector_result.product_id)

        if product is None:
            continue

        if only_in_stock and product.stock <= 0:
            continue

        if category is not None and product.category != category:
            continue

        if brand is not None and product.brand != brand:
            continue

        if max_price is not None and product.price > max_price:
            continue

        results.append(
            SemanticProductResult(
                product=product,
                score=vector_result.score,
            )
        )

    return results
