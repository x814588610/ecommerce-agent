"""数据库连接和会话管理。"""

from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.commerce import approval_models as _approval_models  # noqa: F401
from ecom_agent.commerce import models as _product_models  # noqa: F401
from ecom_agent.commerce import order_models as _order_models  # noqa: F401
from ecom_agent.settings import get_settings

settings = get_settings()


def _ensure_sqlite_directory(database_url: str) -> None:
    """为本地 SQLite 数据库创建父目录。"""

    if not database_url.startswith("sqlite:///"):
        return

    database_path = Path(database_url.removeprefix("sqlite:///"))
    database_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(settings.database_url)

engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """如果数据库表不存在则创建全部表。"""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """为一次请求提供一个数据库会话。"""

    with Session(engine) as session:
        yield session
