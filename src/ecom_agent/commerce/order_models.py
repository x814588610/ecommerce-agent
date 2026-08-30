"""订单相关的数据表模型。"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc)


class OrderRecord(SQLModel, table=True):
    """保存订单基本信息。"""

    __tablename__ = "orders"

    order_id: str = Field(
        primary_key=True,
        max_length=50,
    )
    user_id: str = Field(
        index=True,
        max_length=100,
    )
    status: str = Field(
        default="pending",
        index=True,
        max_length=30,
    )
    total_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        max_digits=12,
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
    )


class OrderItemRecord(SQLModel, table=True):
    """保存订单中的商品明细。"""

    __tablename__ = "order_items"

    order_item_id: int | None = Field(
        default=None,
        primary_key=True,
    )
    order_id: str = Field(
        foreign_key="orders.order_id",
        index=True,
        max_length=50,
    )
    product_id: str = Field(
        max_length=50,
    )
    product_name: str = Field(
        max_length=200,
    )
    quantity: int = Field(
        ge=1,
    )
    unit_price: Decimal = Field(
        ge=0,
        decimal_places=2,
        max_digits=12,
    )