"""订单 API 的请求和响应模型。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemResponse(BaseModel):
    """订单商品明细。"""

    order_item_id: int
    product_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)


class OrderResponse(BaseModel):
    """订单查询响应。"""

    order_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    total_amount: Decimal = Field(ge=0)
    created_at: datetime
    items: list[OrderItemResponse]