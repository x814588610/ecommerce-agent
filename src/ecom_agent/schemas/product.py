"""商品请求和响应模型。"""

from decimal import Decimal

from pydantic import BaseModel, Field


class Product(BaseModel):
    """电商系统展示的商品。"""
    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    brand: str = ""
    description: str = ""
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    tags: list[str] = Field(default_factory=list)


class ProductSearchRequest(BaseModel):
    """商品搜索接口接受的过滤条件。"""

    query: str = Field(min_length=1)
    category: str | None = None
    brand: str | None = None
    max_price: Decimal | None = Field(default=None, ge=0)
    only_in_stock: bool = True


class ProductSearchResponse(BaseModel):
    """结构化商品搜索结果页。"""

    items: list[Product]
    total: int = Field(ge=0)


class SemanticProductItem(BaseModel):
    """带有语义相似度和检索来源的商品。"""

    product: Product
    score: float
    source: str = Field(min_length=1)



class SemanticProductSearchResponse(BaseModel):
    """商品语义搜索结果页。"""

    items: list[SemanticProductItem]
    total: int = Field(ge=0)
