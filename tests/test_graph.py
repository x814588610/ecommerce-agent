"""Tests for the commerce agent graph."""

from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from ecom_agent.agent.graph import build_commerce_graph
from ecom_agent.agent.state import create_initial_state


@tool
def lookup_product(product_id: str) -> str:
    """Look up a fake product for testing."""

    return f"商品：{product_id}"


class FakeModel:
    """A fake model that returns predefined responses."""

    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = list(responses)
        self.calls: list[list[object]] = []
        self.bound_tools: list[object] = []

    def bind_tools(self, tools: list[object]) -> "FakeModel":
        """Record the tools bound to the model."""

        self.bound_tools = list(tools)
        return self

    def invoke(self, messages: list[object]) -> AIMessage:
        """Return the next predefined response."""

        self.calls.append(messages)
        return self.responses.pop(0)


def create_tool_call(call_id: str) -> AIMessage:
    """Create a fake tool-call response."""

    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "lookup_product",
                "args": {"product_id": "phone-001"},
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )


def test_graph_returns_direct_model_answer() -> None:
    """The graph should finish when the model does not request a tool."""

    model = FakeModel(
        [
            AIMessage(content="这是一段直接回答。"),
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    result = graph.invoke(create_initial_state("你好"))

    assert result["answer"] == "这是一段直接回答。"
    assert result["step_count"] == 1
    assert len(model.calls) == 1


def test_graph_calls_tool_then_returns_final_answer() -> None:
    """The graph should execute a tool and then ask the model again."""

    model = FakeModel(
        [
            create_tool_call("call-1"),
            AIMessage(content="商品查询结果已经找到。"),
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    result = graph.invoke(create_initial_state("查询 phone-001"))

    assert result["answer"] == "商品查询结果已经找到。"
    assert result["step_count"] == 2
    assert len(model.calls) == 2
    assert result["messages"][-2].type == "tool"


def test_graph_stops_after_maximum_steps() -> None:
    """The graph should stop safely instead of looping forever."""

    model = FakeModel(
        [
            create_tool_call(f"call-{index}")
            for index in range(6)
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    result = graph.invoke(create_initial_state("不断查询商品"))

    assert result["answer"] == "我暂时无法完成这次查询，请稍后重试。"
    assert result["step_count"] == 6
    assert len(model.calls) == 6