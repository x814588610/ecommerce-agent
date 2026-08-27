"""Agent 请求的安全策略。"""

from typing import Literal

RiskLevel = Literal["low", "high"]

HIGH_RISK_ACTIONS = (
    "我要退款",
    "帮我退款",
    "申请退款",
    "想退款",
    "我要退货",
    "帮我退货",
    "申请退货",
    "取消订单",
    "修改订单",
    "修改收货地址",
    "更改收货地址",
    "帮我下单",
    "我要支付",
    "帮我付款",
)


def assess_risk(user_message: str) -> tuple[RiskLevel, bool]:
    """判断消息是否需要人工审批。"""

    normalized_message = " ".join(user_message.strip().split())

    if any(action in normalized_message for action in HIGH_RISK_ACTIONS):
        return "high", True

    return "low", False
