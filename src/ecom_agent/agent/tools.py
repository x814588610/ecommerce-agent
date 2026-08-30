"""电商业务的 LangChain 工具。"""

import json
from decimal import Decimal

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field
from sqlmodel import Session

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.order_models import (
    OrderItemRecord,
    OrderRecord,
)
from ecom_agent.commerce.order_repository import OrderRepository
from ecom_agent.commerce.repository import ProductRepository
from ecom_agent.retrieval.policy_vector_store import (
    PolicySearchResult,
    PolicyVectorStore,
)
from ecom_agent.retrieval.search import (
    SemanticProductResult,
    search_products_semantically,
)
from ecom_agent.retrieval.vector_store import ProductVectorStore


class ProductSearchToolInput(BaseModel):
    """商品搜索工具接受的输入参数。"""

    query: str = Field(
        default="",
        description="Keywords in the product name or description.",
    )
    category: str | None = Field(
        default=None,
        description="Product category, such as phone or computer.",
    )
    brand: str | None = Field(
        default=None,
        description="Product brand.",
    )
    max_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Maximum acceptable price.",
    )
    only_in_stock: bool = Field(
        default=True,
        description="Whether to exclude out-of-stock products.",
    )


class ProductIdToolInput(BaseModel):
    """商品 ID 工具接受的输入参数。"""

    product_id: str = Field(
        min_length=1,
        description="The unique product ID.",
    )


class OrderIdToolInput(BaseModel):
    """订单查询工具接受的输入参数。"""

    order_id: str = Field(
        min_length=1,
        description="The unique order ID.",
    )


class PolicySearchToolInput(BaseModel):
    """售后政策搜索工具接受的输入参数。"""

    query: str = Field(
        min_length=1,
        description="用户关于退货、换货、退款或保修的问题。",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=10,
        description="最多返回的政策数量。",
    )


def _serialize_product(record: ProductRecord) -> dict[str, object]:
    """将数据库记录转换为 JSON 兼容的数据。"""

    return {
        "product_id": record.product_id,
        "name": record.name,
        "category": record.category,
        "brand": record.brand,
        "description": record.description,
        "price": str(record.price),
        "stock": record.stock,
        "tags": json.loads(record.tags_json),
    }


def _serialize_order(
    order: OrderRecord,
    items: list[OrderItemRecord],
) -> dict[str, object]:
    """将订单记录转换为 JSON 兼容的数据。"""

    return {
        "order_id": order.order_id,
        "status": order.status,
        "total_amount": str(order.total_amount),
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "order_item_id": item.order_item_id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
            }
            for item in items
        ],
    }


def _order_not_found(order_id: str) -> str:
    """返回机器可读的订单不存在结果。"""

    return json.dumps(
        {
            "error": "order_not_found",
            "order_id": order_id,
        },
        ensure_ascii=False,
    )


def _serialize_policy_result(
    result: PolicySearchResult,
) -> dict[str, object]:
    """将政策搜索结果转换为 JSON 兼容的数据。"""

    return {
        "policy_id": result.policy_id,
        "title": result.payload.get("title", ""),
        "content": result.payload.get("content", ""),
        "score": result.score,
        "source": result.payload.get("source", ""),
    }


def _product_not_found(product_id: str) -> str:
    """返回机器可读的商品不存在结果。"""

    return json.dumps(
        {
            "error": "product_not_found",
            "product_id": product_id,
        },
        ensure_ascii=False,
    )


def create_product_search_tool(session: Session) -> StructuredTool:
    """创建一个由数据库会话支持的 LangChain 工具。"""

    repository = ProductRepository(session)

    @tool(args_schema=ProductSearchToolInput)
    def search_products(
        query: str = "",
        category: str | None = None,
        brand: str | None = None,
        max_price: Decimal | None = None,
        only_in_stock: bool = True,
    ) -> str:
        """按关键词、类别、品牌、价格和库存搜索商品。"""

        records = repository.search(
            query=query,
            category=category,
            brand=brand,
            max_price=max_price,
            only_in_stock=only_in_stock,
        )
        products = [_serialize_product(record) for record in records]

        return json.dumps(products, ensure_ascii=False)

    return search_products


def create_product_detail_tool(session: Session) -> StructuredTool:
    """创建一个用于获取商品详情的 LangChain 工具。"""

    repository = ProductRepository(session)

    @tool(args_schema=ProductIdToolInput)
    def get_product_detail(product_id: str) -> str:
        """返回一个商品的完整详情。"""

        record = repository.get_by_id(product_id)

        if record is None:
            return _product_not_found(product_id)

        return json.dumps(
            _serialize_product(record),
            ensure_ascii=False,
        )

    return get_product_detail


def create_inventory_tool(session: Session) -> StructuredTool:
    """创建一个用于查询商品库存的 LangChain 工具。"""

    repository = ProductRepository(session)

    @tool(args_schema=ProductIdToolInput)
    def check_inventory(product_id: str) -> str:
        """返回一个商品的当前库存状态。"""

        record = repository.get_by_id(product_id)

        if record is None:
            return _product_not_found(product_id)

        inventory = {
            "product_id": record.product_id,
            "name": record.name,
            "stock": record.stock,
            "in_stock": record.stock > 0,
        }
        return json.dumps(inventory, ensure_ascii=False)

    return check_inventory


def create_policy_search_tool(
    vector_store: PolicyVectorStore,
) -> StructuredTool:
    """创建一个用于搜索售后政策的 LangChain 工具。"""

    @tool(args_schema=PolicySearchToolInput)
    def search_policy(
        query: str,
        limit: int = 5,
    ) -> str:
        """根据用户问题搜索相关售后政策。"""

        results = vector_store.search(
            query=query,
            limit=limit,
        )
        items = [_serialize_policy_result(result) for result in results]

        return json.dumps(
            {
                "items": items,
                "total": len(items),
            },
            ensure_ascii=False,
        )

    return search_policy


class SemanticProductSearchToolInput(BaseModel):
    """商品语义搜索工具接受的输入参数。"""

    query: str = Field(
        min_length=1,
        description="用户对商品需求的自然语言描述。",
    )
    category: str | None = Field(
        default=None,
        description="商品类别，例如手机或电脑。",
    )
    brand: str | None = Field(
        default=None,
        description="商品品牌。",
    )
    max_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="用户能够接受的最高价格。",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="最多返回的商品数量。",
    )
    only_in_stock: bool = Field(
        default=True,
        description="是否排除缺货商品。",
    )


def _serialize_semantic_result(
    result: SemanticProductResult,
) -> dict[str, object]:
    """将语义搜索结果转换为 JSON 兼容的数据。"""

    return {
        "product": _serialize_product(result.product),
        "score": result.score,
        "source": result.source,
    }


def create_semantic_product_search_tool(
    session: Session,
    vector_store: ProductVectorStore,
) -> StructuredTool:
    """创建一个用于商品语义搜索的 LangChain 工具。"""

    @tool(args_schema=SemanticProductSearchToolInput)
    def semantic_search_products(
        query: str,
        category: str | None = None,
        brand: str | None = None,
        max_price: Decimal | None = None,
        limit: int = 5,
        only_in_stock: bool = True,
    ) -> str:
        """根据用户自然语言需求搜索相关商品。"""

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
        items = [_serialize_semantic_result(result) for result in results]

        return json.dumps(
            {
                "items": items,
                "total": len(items),
            },
            ensure_ascii=False,
        )

    return semantic_search_products


def create_order_query_tool(
    session: Session,
    user_id: str,
) -> StructuredTool:
    """创建一个只查询当前用户订单的 LangChain 工具。"""

    repository = OrderRepository(session)

    @tool(args_schema=OrderIdToolInput)
    def get_order_status(order_id: str) -> str:
        """查询当前用户订单的状态和商品明细。"""

        order = repository.get_by_id_for_user(
            order_id=order_id,
            user_id=user_id,
        )

        if order is None:
            return _order_not_found(order_id)

        items = repository.list_items(order.order_id)

        return json.dumps(
            _serialize_order(order, items),
            ensure_ascii=False,
        )

    return get_order_status
