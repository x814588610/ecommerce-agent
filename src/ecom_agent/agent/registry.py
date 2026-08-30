"""电商 Agent 可用工具的注册表。"""

from langchain_core.tools import StructuredTool
from sqlmodel import Session

from ecom_agent.agent.tools import (
    create_inventory_tool,
    create_order_query_tool,
    create_policy_search_tool,
    create_product_detail_tool,
    create_product_search_tool,
    create_semantic_product_search_tool,
)
from ecom_agent.retrieval.policy_vector_store import PolicyVectorStore
from ecom_agent.retrieval.vector_store import ProductVectorStore


def create_commerce_tools(
    session: Session,
    vector_store: ProductVectorStore,
    policy_vector_store: PolicyVectorStore,
    user_id: str,
) -> list[StructuredTool]:
    """为一个数据库会话创建全部电商工具。"""

    return [
        create_product_search_tool(session),
        create_semantic_product_search_tool(session, vector_store),
        create_product_detail_tool(session),
        create_inventory_tool(session),
        create_policy_search_tool(policy_vector_store),
        create_order_query_tool(session, user_id),
    ]
