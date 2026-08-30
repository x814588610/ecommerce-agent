"""HTTP API 入口。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

from ecom_agent.api.approvals import router as approvals_router
from ecom_agent.api.chat import router as chat_router
from ecom_agent.api.orders import router as orders_router
from ecom_agent.api.products import router as products_router
from ecom_agent.commerce.database import create_db_and_tables, engine
from ecom_agent.commerce.seed import seed_orders, seed_products
from ecom_agent.logging_config import setup_logging
from ecom_agent.settings import get_settings

settings = get_settings()



@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """应用启动时初始化资源。"""

    setup_logging()
    create_db_and_tables()

    with Session(engine) as session:
        seed_products(session)
        seed_orders(session)

    yield



app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(products_router)
app.include_router(chat_router)
app.include_router(approvals_router)
app.include_router(orders_router)

@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """返回服务健康状态。"""

    return {
        "status": "ok",
        "environment": settings.app_env,
    }
