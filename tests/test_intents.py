"""测试电商请求意图分类。"""

import pytest

from ecom_agent.agent.intents import (
    classify_intent,
    is_tool_allowed,
)


@pytest.mark.parametrize(
    ("message", "expected_intent"),
    [
        ("推荐适合学生的手机", "semantic_search"),
        ("我想买一部手机", "semantic_search"),
        ("3000 元以内有什么推荐", "semantic_search"),
        ("学习手机还有库存吗", "inventory"),
        ("这个商品有现货吗", "inventory"),
        ("旗舰手机的详细参数", "product_detail"),
        ("这部手机多少钱", "product_detail"),
        ("你好", "general"),
        ("退款政策是什么", "policy"),
        ("这个商品支持退货吗", "policy"),
        ("售后保修多久", "policy"),
        ("查询订单 order-001 的状态", "order_query"),
        ("我的订单物流到哪里了", "order_query"),
        ("订单什么时候发货", "order_query"),
        ("我要申请退款", "general"),
        ("帮我取消订单", "general"),
        ("", "general"),
    ],
)
def test_classify_intent(
    message: str,
    expected_intent: str,
) -> None:
    """不同类型的用户消息应该得到对应意图。"""

    assert classify_intent(message) == expected_intent


def test_stock_filter_does_not_override_search_intent() -> None:
    """搜索请求中的库存条件不应该改变商品搜索意图。"""

    assert classify_intent("推荐一部现在有库存的手机") == "semantic_search"


@pytest.mark.parametrize(
    ("intent", "tool_name", "available_tool_names", "expected"),
    [
        ("policy", "search_policy", ["search_policy"], True),
        (
            "policy",
            "search_products",
            ["search_policy", "search_products"],
            False,
        ),
    ],
)
def test_policy_tool_permissions(
    intent: str,
    tool_name: str,
    available_tool_names: list[str],
    expected: bool,
) -> None:
    """售后意图应该只允许调用售后政策工具。"""

    assert (
        is_tool_allowed(
            intent,
            tool_name,
            available_tool_names,
        )
        is expected
    )


def test_order_tool_permissions() -> None:
    """订单意图只能调用订单查询工具。"""

    assert is_tool_allowed(
        "order_query",
        "get_order_status",
        ["get_order_status"],
    )

    assert not is_tool_allowed(
        "order_query",
        "search_products",
        ["get_order_status", "search_products"],
    )
