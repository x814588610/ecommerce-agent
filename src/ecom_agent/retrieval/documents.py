"""为语义检索准备商品记录。"""

import json
from dataclasses import dataclass

from ecom_agent.commerce.models import ProductRecord


@dataclass(frozen=True, slots=True)
class ProductDocument:
    """为向量数据库准备的商品文档。"""

    product_id: str
    text: str
    payload: dict[str, object]


def build_product_document(product: ProductRecord) -> ProductDocument:
    """将一条数据库商品记录转换为可供检索的数据。"""

    try:
        tags = json.loads(product.tags_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid tags JSON for product: {product.product_id}"
        ) from exc

    if not isinstance(tags, list):
        raise ValueError(
            f"Product tags must be a JSON list: {product.product_id}"
        )

    tags_text = ", ".join(str(tag) for tag in tags)

    text = "\n".join(
        [
            f"商品名称：{product.name}",
            f"商品类别：{product.category}",
            f"品牌：{product.brand}",
            f"商品描述：{product.description}",
            f"商品标签：{tags_text}",
        ]
    )

    payload = {
        "product_id": product.product_id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "description": product.description,
        "price": str(product.price),
        "price_value": float(product.price),
        "stock": product.stock,
        "tags": tags,
    }

    return ProductDocument(
        product_id=product.product_id,
        text=text,
        payload=payload,
    )
