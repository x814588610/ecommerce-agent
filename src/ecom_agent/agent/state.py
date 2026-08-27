"""电商 Agent 的状态定义。"""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """在 LangGraph 节点之间传递的共享状态。"""

    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str
    session_id: str
    intent: str
    search_query: str
    tool_results: list[dict[str, object]]
    answer: str
    risk_level: str
    approval_required: bool
    error: str | None
    step_count: int


def create_initial_state(
    user_message: str,
    session_id: str = "default-session",
    user_id: str = "anonymous",
) -> AgentState:
    """为新会话创建完整的初始化状态。"""

    return {
        "messages": [
            {
                "role": "user",
                "content": user_message,
            }
        ],
        "user_id": user_id,
        "session_id": session_id,
        "intent": "",
        "search_query": "",
        "tool_results": [],
        "answer": "",
        "risk_level": "low",
        "approval_required": False,
        "error": None,
        "step_count": 0,
    }
