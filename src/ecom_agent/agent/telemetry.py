"""记录 Agent 的模型调用、工具调用和异常信息。"""

import logging
from collections.abc import Sequence

logger = logging.getLogger("ecom_agent.agent")


def log_model_call(
    *,
    tool_names: Sequence[str],
    elapsed_ms: float,
) -> None:
    """记录一次模型调用。"""

    bound_tools = ",".join(tool_names) or "none"

    logger.info(
        "model_call tools=%s elapsed_ms=%.2f",
        bound_tools,
        elapsed_ms,
    )


def log_tool_call(
    *,
    tool_name: str,
    elapsed_ms: float,
    success: bool,
) -> None:
    """记录一次工具调用。"""

    logger.info(
        "tool_call name=%s success=%s elapsed_ms=%.2f",
        tool_name,
        success,
        elapsed_ms,
    )


def log_agent_error(error: Exception) -> None:
    """只记录 Agent 异常类型，避免泄露敏感信息。"""

    logger.error(
        "agent_error type=%s",
        type(error).__name__,
    )