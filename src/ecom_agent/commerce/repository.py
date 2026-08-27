"""商品数据库操作。"""

from decimal import Decimal

from sqlmodel import Session, select

from ecom_agent.commerce.models import ProductRecord


class ProductRepository:
    """提供商品数据库操作。"""

    def __init__(self, session: Session) -> None:
        """保存仓库使用的数据库会话。"""

        self.session = session

    def add(self, product: ProductRecord) -> ProductRecord:
        """保存一个商品并返回保存后的对象。"""

        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def get_by_id(self, product_id: str) -> ProductRecord | None:
        """根据 ID 返回商品；不存在时返回 None。"""

        return self.session.get(ProductRecord, product_id)

    def list_all(self) -> list[ProductRecord]:
        """返回按名称排序的所有商品。"""

        statement = select(ProductRecord).order_by(ProductRecord.name)
        return list(self.session.exec(statement).all())

    def search(
        self,
        query: str = "",
        category: str | None = None,
        brand: str | None = None,
        max_price: Decimal | None = None,
        only_in_stock: bool = True,
    ) -> list[ProductRecord]:
        """使用可选条件搜索商品。"""

        statement = select(ProductRecord)

        if query:
            statement = statement.where(
                ProductRecord.name.contains(query)
                | ProductRecord.description.contains(query)
            )

        if category:
            statement = statement.where(ProductRecord.category == category)

        if brand:
            statement = statement.where(ProductRecord.brand == brand)

        if max_price is not None:
            statement = statement.where(ProductRecord.price <= max_price)

        if only_in_stock:
            statement = statement.where(ProductRecord.stock > 0)

        statement = statement.order_by(ProductRecord.name)
        return list(self.session.exec(statement).all())
