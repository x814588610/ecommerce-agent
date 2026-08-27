"""商品查询 API 路由。"""

import json
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ecom_agent.commerce.database import get_session
from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.factory import get_product_vector_store
from ecom_agent.retrieval.search import (
    SemanticProductResult,
    search_products_semantically,
)
from ecom_agent.retrieval.vector_store import ProductVectorStore
from ecom_agent.schemas.product import (
    Product,
    ProductSearchResponse,
    SemanticProductItem,
    SemanticProductSearchResponse,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


def _to_product(record: ProductRecord) -> Product:
    """将数据库记录转换为 API 响应模型。"""

    return Product(
        product_id=record.product_id,
        name=record.name,
        category=record.category,
        brand=record.brand,
        description=record.description,
        price=record.price,
        stock=record.stock,
        tags=json.loads(record.tags_json),
    )

def _to_semantic_item(result: SemanticProductResult) -> SemanticProductItem:
    """将语义搜索结果转换为 API 响应模型。"""

    return SemanticProductItem(
        product=_to_product(result.product),
        score=result.score,
        source=result.source,
    )




@router.get("", response_model=ProductSearchResponse)
def search_products(
    session: Annotated[Session, Depends(get_session)],
    query: str = "",
    category: str | None = None,
    brand: str | None = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    only_in_stock: bool = True,
) -> ProductSearchResponse:
    """使用可选过滤条件搜索商品。"""

    repository = ProductRepository(session)
    records = repository.search(
        query=query,
        category=category,
        brand=brand,
        max_price=max_price,
        only_in_stock=only_in_stock,
    )
    products = [_to_product(record) for record in records]

    return ProductSearchResponse(
        items=products,
        total=len(products),
    )

@router.get(
    "/semantic",
    response_model=SemanticProductSearchResponse,
)
def semantic_search_products(
    session: Annotated[Session, Depends(get_session)],
    vector_store: Annotated[
        ProductVectorStore,
        Depends(get_product_vector_store),
    ],
    query: Annotated[str, Query(min_length=1)],
    category: str | None = None,
    brand: str | None = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
    only_in_stock: bool = True,
) -> SemanticProductSearchResponse:
    """使用向量相似度搜索商品。"""

    results = search_products_semantically(
        session=session,
        vector_store=vector_store,
        query=query,
        limit=limit,
        only_in_stock=only_in_stock,
        category=category,
        brand=brand,
        max_price=max_price,
    )
    items = [_to_semantic_item(result) for result in results]

    return SemanticProductSearchResponse(
        items=items,
        total=len(items),
    )




@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> Product:
    """根据 ID 返回一个商品。"""

    repository = ProductRepository(session)
    record = repository.get_by_id(product_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return _to_product(record)
