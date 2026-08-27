"""测试 Agent 调用观测。"""

import logging

from ecom_agent.agent.telemetry import (
    log_agent_error,
    log_model_call,
    log_tool_call,
)


def test_log_model_call(caplog) -> None:
    """模型调用日志应该包含工具名称和耗时。"""

    with caplog.at_level(
        logging.INFO,
        logger="ecom_agent.agent",
    ):
        log_model_call(
            tool_names=["search_policy"],
            elapsed_ms=12.34,
        )

    assert "model_call" in caplog.text
    assert "search_policy" in caplog.text
    assert "12.34" in caplog.text


def test_log_tool_call(caplog) -> None:
    """工具调用日志应该包含名称、状态和耗时。"""

    with caplog.at_level(
        logging.INFO,
        logger="ecom_agent.agent",
    ):
        log_tool_call(
            tool_name="check_inventory",
            elapsed_ms=8.5,
            success=True,
        )

    assert "tool_call" in caplog.text
    assert "check_inventory" in caplog.text
    assert "True" in caplog.text
    assert "8.50" in caplog.text


def test_log_agent_error_does_not_include_api_key(caplog) -> None:
    """异常日志不应该记录 API Key。"""

    secret = "sk-test-secret"

    with caplog.at_level(
        logging.ERROR,
        logger="ecom_agent.agent",
    ):
        log_agent_error(
            RuntimeError(f"请求失败，密钥为 {secret}")
        )

    assert "agent_error" in caplog.text
    assert secret not in caplog.text