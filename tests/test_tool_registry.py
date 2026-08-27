"""Tests for the commerce tool registry."""

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.agent.registry import create_commerce_tools


def create_test_session() -> Session:
    """Create an empty in-memory database session."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_create_commerce_tools_returns_all_tools() -> None:
    """The registry should return all tools in order."""

    with create_test_session() as session:
        fake_vector_store = object()
        fake_policy_vector_store = object()

        tools = create_commerce_tools(
            session,
            fake_vector_store,
            fake_policy_vector_store,
        )

    assert [tool.name for tool in tools] == [
        "search_products",
        "semantic_search_products",
        "get_product_detail",
        "check_inventory",
        "search_policy",
    ]