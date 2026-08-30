"""订单查询 API 路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ecom_agent.commerce.database import get_session
from ecom_agent.commerce.order_models import OrderRecord
from ecom_agent.commerce.order_repository import OrderRepository
from ecom_agent.schemas.order import (
    OrderItemResponse,
    OrderResponse,
)

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


def _to_response(
    order: OrderRecord,
    repository: OrderRepository,
) -> OrderResponse:
    """将数据库订单转换为 API 响应。"""

    items = repository.list_items(order.order_id)

    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[
            OrderItemResponse(
                order_item_id=item.order_item_id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in items
        ],
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: str,
    user_id: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
        ),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> OrderResponse:
    """查询当前用户自己的订单。"""

    repository = OrderRepository(session)
    order = repository.get_by_id_for_user(
        order_id=order_id,
        user_id=user_id,
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return _to_response(order, repository)