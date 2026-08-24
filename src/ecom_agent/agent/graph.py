"""LangGraph workflow for the commerce agent."""

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from ecom_agent.agent.state import AgentState
from ecom_agent.llm.prompts import CUSTOMER_SERVICE_SYSTEM_PROMPT

MAX_AGENT_STEPS = 6


def _has_tool_calls(message: object) -> bool:
    """Check whether the model requested any tools."""

    return bool(getattr(message, "tool_calls", []))


def _content_to_text(content: object) -> str:
    """Convert model content into text for the final answer."""

    if isinstance(content, str):
        return content

    return str(content)


def build_commerce_graph(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
) -> CompiledStateGraph:
    """Build and compile the commerce agent graph."""

    tool_list = list(tools)

    if not tool_list:
        raise ValueError("At least one commerce tool is required.")

    model_with_tools = model.bind_tools(tool_list)

    def agent_node(state: AgentState) -> dict[str, object]:
        """Call the model once."""

        messages = [
            SystemMessage(content=CUSTOMER_SERVICE_SYSTEM_PROMPT),
            *state.get("messages", []),
        ]

        response = model_with_tools.invoke(messages)
        step_count = state.get("step_count", 0) + 1

        updates: dict[str, object] = {
            "messages": [response],
            "step_count": step_count,
        }

        if not _has_tool_calls(response):
            updates["answer"] = _content_to_text(response.content)

        return updates

    def max_steps_node(state: AgentState) -> dict[str, object]:
        """Return a safe answer when the loop reaches its limit."""

        response = AIMessage(
            content="我暂时无法完成这次查询，请稍后重试。"
        )

        return {
            "messages": [response],
            "answer": response.content,
        }

    def route_after_agent(state: AgentState) -> str:
        """Choose whether to call tools, stop, or exit safely."""

        messages = state.get("messages", [])
        if not messages:
            return END

        last_message = messages[-1]

        if _has_tool_calls(last_message):
            if state.get("step_count", 0) >= MAX_AGENT_STEPS:
                return "max_steps"

            return "tools"

        return END

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tool_list))
    workflow.add_node("max_steps", max_steps_node)

    workflow.add_edge(START, "agent")

    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "max_steps": "max_steps",
            END: END,
        },
    )

    workflow.add_edge("tools", "agent")
    workflow.add_edge("max_steps", END)

    return workflow.compile()