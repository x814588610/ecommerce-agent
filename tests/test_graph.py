"""Tests for the commerce agent graph."""
import logging

from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from ecom_agent.agent.graph import build_commerce_graph
from ecom_agent.agent.state import create_initial_state


@tool
def lookup_product(product_id: str) -> str:
    """Look up a fake product for testing."""

    return f"商品：{product_id}"


@tool
def failing_product_lookup(product_id: str) -> str:
    """模拟商品工具异常。"""

    raise RuntimeError("测试工具异常")

@tool
def search_products(query: str) -> str:
    """模拟关键词搜索没有找到商品。"""

    return "[]"


@tool
def semantic_search_products(query: str) -> str:
    """模拟语义搜索没有找到商品。"""

    return '{"items": [], "total": 0}'


@tool
def search_policy(query: str) -> str:
    """模拟售后政策搜索。"""

    return (
        '{"items": [{"policy_id": "refund-policy", '
        '"title": "退款政策", '
        '"content": "退货审核通过后，通常需要 3 到 7 个工作日到账。", '
        '"score": 0.94, '
        '"source": "本地售后政策"}], "total": 1}'
    )

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


def test_graph_classifies_intent_before_model() -> None:
    """图应该在调用模型前识别用户意图。"""

    model = FakeModel(
        [
            AIMessage(content="推荐结果已经找到。"),
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    result = graph.invoke(
        create_initial_state("推荐适合学生学习的手机")
    )

    assert result["intent"] == "semantic_search"
    assert result["answer"] == "推荐结果已经找到。"
    assert "当前请求意图：semantic_search" in model.calls[0][0].content

def test_graph_blocks_tool_not_allowed_by_intent() -> None:
    """库存意图不应该调用商品查询工具。"""

    model = FakeModel(
        [
            create_tool_call("blocked-call"),
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    result = graph.invoke(
        create_initial_state("这个手机还有库存吗")
    )

    assert result["intent"] == "inventory"
    assert result["answer"] == (
        "当前请求与工具不匹配，我暂时无法执行该操作。"
    )
    assert len(model.calls) == 1


def test_graph_returns_friendly_answer_when_tool_fails() -> None:
    """工具异常时，图应该返回友好回答并记录错误。"""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "failing_product_lookup",
                        "args": {"product_id": "phone-001"},
                        "id": "error-call",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    graph = build_commerce_graph(model, [failing_product_lookup])

    result = graph.invoke(create_initial_state("查询商品"))

    assert result["answer"] == "商品查询暂时不可用，请稍后重试。"
    assert result["error"] == "测试工具异常"
    assert result["step_count"] == 1
    assert len(model.calls) == 1



def test_graph_handles_empty_keyword_search_result() -> None:
    """关键词搜索无结果时，图应该返回固定提示。"""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_products",
                        "args": {"query": "不存在的手机"},
                        "id": "empty-keyword-call",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    graph = build_commerce_graph(model, [search_products])

    result = graph.invoke(
        create_initial_state("帮我找一款不存在的手机")
    )

    assert result["answer"] == (
        "没有找到符合条件的商品，你可以调整关键词、品牌或价格范围后重试。"
    )
    assert result["error"] is None
    assert result["step_count"] == 1
    assert len(model.calls) == 1
    assert result["messages"][-1].type == "tool"


def test_graph_handles_empty_semantic_search_result() -> None:
    """语义搜索无结果时，图应该返回固定提示。"""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "semantic_search_products",
                        "args": {"query": "适合在月球使用的手机"},
                        "id": "empty-semantic-call",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    graph = build_commerce_graph(
        model,
        [semantic_search_products],
    )

    result = graph.invoke(
        create_initial_state("推荐适合在月球使用的手机")
    )

    assert result["answer"] == (
        "没有找到符合条件的商品，你可以调整关键词、品牌或价格范围后重试。"
    )
    assert result["error"] is None
    assert result["step_count"] == 1
    assert len(model.calls) == 1
    assert result["messages"][-1].type == "tool"


def test_graph_allows_policy_tool_for_policy_intent() -> None:
    """售后政策意图应该允许调用售后政策工具。"""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_policy",
                        "args": {"query": "退款政策通常多久到账？"},
                        "id": "policy-call",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="退款审核通过后，通常需要 3 到 7 个工作日到账。"
            ),
        ]
    )
    graph = build_commerce_graph(model, [search_policy])

    result = graph.invoke(
        create_initial_state("退款政策通常多久到账？")
    )

    assert result["intent"] == "policy"
    assert result["answer"] == (
        "退款审核通过后，通常需要 3 到 7 个工作日到账。"
    )
    assert result["step_count"] == 2
    assert len(model.calls) == 2
    assert result["messages"][-2].type == "tool"
    assert "退款政策" in result["messages"][-2].content



def test_graph_blocks_product_tool_for_policy_intent() -> None:
    """售后政策意图不应该调用商品查询工具。"""

    model = FakeModel(
        [
            create_tool_call("blocked-policy-call"),
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    result = graph.invoke(
        create_initial_state("退款政策是什么？")
    )

    assert result["intent"] == "policy"
    assert result["answer"] == (
        "当前请求与工具不匹配，我暂时无法执行该操作。"
    )
    assert result["step_count"] == 1
    assert len(model.calls) == 1



def test_graph_logs_model_and_tool_calls(caplog) -> None:
    """图应该记录模型和工具调用日志。"""

    model = FakeModel(
        [
            create_tool_call("telemetry-call"),
            AIMessage(content="商品查询完成。"),
        ]
    )
    graph = build_commerce_graph(model, [lookup_product])

    with caplog.at_level(
        logging.INFO,
        logger="ecom_agent.agent",
    ):
        result = graph.invoke(
            create_initial_state("查询 phone-001")
        )

    assert result["answer"] == "商品查询完成。"
    assert "model_call" in caplog.text
    assert "tool_call" in caplog.text
    assert "lookup_product" in caplog.text
    assert "elapsed_ms=" in caplog.text