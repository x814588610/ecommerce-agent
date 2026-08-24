"""Database operations for products."""

from decimal import Decimal

from sqlmodel import Session, select

from ecom_agent.commerce.models import ProductRecord


class ProductRepository:
    """Provide database operations for products."""

    def __init__(self, session: Session) -> None:
        """Store the database session used by this repository."""

        self.session = session

    def add(self, product: ProductRecord) -> ProductRecord:
        """Save one product and return the saved object."""

        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def get_by_id(self, product_id: str) -> ProductRecord | None:
        """Return one product by ID, or None if it does not exist."""

        return self.session.get(ProductRecord, product_id)

    def list_all(self) -> list[ProductRecord]:
        """Return all products sorted by name."""

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
        """Search products with optional filters."""

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