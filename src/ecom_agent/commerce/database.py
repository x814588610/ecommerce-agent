"""Database connection and session management."""

from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, create_engine

from ecom_agent.commerce.models import ProductRecord
from ecom_agent.settings import get_settings

settings = get_settings()


def _ensure_sqlite_directory(database_url: str) -> None:
    """Create the parent directory for a local SQLite database."""

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
    """Create all database tables if they do not already exist."""

    ProductRecord.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Provide one database session for a request."""

    with Session(engine) as session:
        yield session