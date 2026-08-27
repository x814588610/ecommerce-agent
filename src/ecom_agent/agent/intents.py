"""识别电商 Agent 请求的基础意图。"""

from collections.abc import Sequence
from typing import Literal

Intent = Literal[
    "semantic_search",
    "product_detail",
    "inventory",
    "policy",
    "general",
]


def classify_intent(user_message: str) -> Intent:
    """根据用户消息中的关键词识别基础意图。"""

    normalized_message = " ".join(user_message.strip().split())

    if not normalized_message:
        return "general"

    
    policy_query_keywords = (
        "售后",
        "退款政策",
        "退货政策",
        "换货政策",
        "退换货",
        "退货规则",
        "退款规则",
        "售后规则",
        "保修",
        "质保",
        "支持退货",
        "支持换货",
    )

    if any(
        keyword in normalized_message
        for keyword in policy_query_keywords
    ):
        return "policy"


    inventory_query_keywords = (
        "库存吗",
        "有库存吗",
        "库存情况",
        "库存数量",
        "库存状态",
        "有货吗",
        "现货吗",
        "是否有库存",
        "还有多少",
        "查库存",
        "查询库存",
    )

    if any(
        keyword in normalized_message
        for keyword in inventory_query_keywords
    ):
        return "inventory"

    if any(
        keyword in normalized_message
        for keyword in ("详情", "参数", "配置", "规格", "价格", "多少钱")
    ):
        return "product_detail"

    if any(
        keyword in normalized_message
        for keyword in ("推荐", "适合", "想买", "购买", "预算", "找一款", "找一部")
    ):
        return "semantic_search"

    return "general"



TOOL_NAMES_BY_INTENT: dict[Intent, frozenset[str]] = {
    "semantic_search": frozenset(
        {
            "semantic_search_products",
            "search_products",
        }
    ),
    "product_detail": frozenset(
        {
            "get_product_detail",
        }
    ),
    "inventory": frozenset(
        {
            "check_inventory",
        }
    ),
    "policy": frozenset(
        {
            "search_policy",
        }
    ),
    "general": frozenset(),
}


def is_tool_allowed(
    intent: str,
    tool_name: str,
    available_tool_names: Sequence[str],
) -> bool:
    """判断当前意图是否允许调用指定工具。"""

    available_names = set(available_tool_names)

    if intent == "general":
        return tool_name in available_names

    allowed_names = TOOL_NAMES_BY_INTENT.get(intent, frozenset())
    return tool_name in allowed_names
