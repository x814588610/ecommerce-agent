"""Tests for agent safety policies."""

import pytest

from ecom_agent.agent.policies import assess_risk


@pytest.mark.parametrize(
    "user_message",
    [
        "我想申请退款",
        "帮我取消订单",
        "我要修改收货地址",
        "帮我付款",
    ],
)
def test_high_risk_actions_require_approval(user_message: str) -> None:
    """High-risk operations should require human approval."""

    risk_level, approval_required = assess_risk(user_message)

    assert risk_level == "high"
    assert approval_required is True


@pytest.mark.parametrize(
    "user_message",
    [
        "退款政策是什么？",
        "这个商品支持退货吗？",
        "我想查询订单状态",
        "推荐一部手机",
    ],
)
def test_information_requests_are_low_risk(user_message: str) -> None:
    """Information requests should not require approval."""

    risk_level, approval_required = assess_risk(user_message)

    assert risk_level == "low"
    assert approval_required is False


def test_risk_policy_ignores_extra_whitespace() -> None:
    """Whitespace should not change the risk assessment."""

    risk_level, approval_required = assess_risk("  我想   申请退款  ")

    assert risk_level == "high"
    assert approval_required is True