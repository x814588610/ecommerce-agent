"""Registry of tools available to the commerce agent."""

from langchain_core.tools import StructuredTool
from sqlmodel import Session

from ecom_agent.agent.tools import (
    create_inventory_tool,
    create_product_detail_tool,
    create_product_search_tool,
)


def create_commerce_tools(session: Session) -> list[StructuredTool]:
    """Create all commerce tools for one database session."""

    return [
        create_product_search_tool(session),
        create_product_detail_tool(session),
        create_inventory_tool(session),
    ]