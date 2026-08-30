"""订单数据库操作。"""

from sqlmodel import Session, select

from ecom_agent.commerce.order_models import (
    OrderItemRecord,
    OrderRecord,
)


class OrderRepository:
    """提供订单查询和保存功能。"""

    def __init__(self, session: Session) -> None:
        """保存数据库会话。"""

        self.session = session

    def add(
        self,
        order: OrderRecord,
        items: list[OrderItemRecord],
    ) -> OrderRecord:
        """保存订单和订单商品。"""

        try:
            self.session.add(order)
            self.session.add_all(items)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(order)
        return order

    def list_all(self) -> list[OrderRecord]:
        """返回全部订单。"""

        statement = select(OrderRecord).order_by(
            OrderRecord.created_at.desc(),
        )
        return list(self.session.exec(statement).all())

    def get_by_id_for_user(
        self,
        order_id: str,
        user_id: str,
    ) -> OrderRecord | None:
        """只返回属于指定用户的订单。"""

        statement = select(OrderRecord).where(
            OrderRecord.order_id == order_id,
            OrderRecord.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def list_items(self, order_id: str) -> list[OrderItemRecord]:
        """返回指定订单中的商品明细。"""

        statement = select(OrderItemRecord).where(
            OrderItemRecord.order_id == order_id,
        ).order_by(OrderItemRecord.order_item_id)

        return list(self.session.exec(statement).all())