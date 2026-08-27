"""使用演示商品填充本地数据库。"""

from decimal import Decimal

from sqlmodel import Session

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository


def seed_products(session: Session) -> int:
    """数据库为空时插入演示商品。"""

    repository = ProductRepository(session)

    if repository.list_all():
        return 0

    products = [
        ProductRecord(
            product_id="phone-001",
            name="学习手机",
            category="手机",
            brand="星河",
            description="适合学生学习和日常使用的入门手机。",
            price=Decimal("1999.00"),
            stock=20,
            tags_json='["学生", "学习", "入门"]',
        ),
        ProductRecord(
            product_id="phone-002",
            name="旗舰手机 Pro",
            category="手机",
            brand="星河",
            description="性能强劲，适合游戏、摄影和高强度使用。",
            price=Decimal("4999.00"),
            stock=8,
            tags_json='["旗舰", "游戏", "摄影"]',
        ),
        ProductRecord(
            product_id="laptop-001",
            name="轻薄办公本",
            category="电脑",
            brand="远山",
            description="重量较轻，适合办公、编程和大学生学习。",
            price=Decimal("4299.00"),
            stock=15,
            tags_json='["轻薄", "办公", "编程"]',
        ),
        ProductRecord(
            product_id="keyboard-001",
            name="机械键盘",
            category="电脑配件",
            brand="云轴",
            description="适合编程和办公使用的机械键盘。",
            price=Decimal("299.00"),
            stock=30,
            tags_json='["键盘", "编程", "办公"]',
        ),
        ProductRecord(
            product_id="headphone-001",
            name="降噪耳机",
            category="耳机",
            brand="静界",
            description="适合学习、通勤和长时间佩戴的降噪耳机。",
            price=Decimal("599.00"),
            stock=0,
            tags_json='["降噪", "学习", "通勤"]',
        ),
    ]

    for product in products:
        repository.add(product)

    return len(products)
