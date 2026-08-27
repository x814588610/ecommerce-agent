"""聊天请求和响应模型。"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """发送给电商 Agent 的用户消息。"""

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's message.",
    )
    session_id: str = Field(
        default="default-session",
        min_length=1,
        max_length=100,
        description="Conversation session ID.",
    )
    user_id: str = Field(
        default="anonymous",
        min_length=1,
        max_length=100,
        description="User ID.",
    )


class ChatResponse(BaseModel):
    """电商 Agent 返回的最终响应。"""

    answer: str = Field(
        min_length=1,
        description="The agent's final answer.",
    )
    session_id: str = Field(
        min_length=1,
        description="Conversation session ID.",
    )
    step_count: int = Field(
        ge=0,
        description="Number of model steps used.",
    )
    risk_level: Literal["low", "high"] = Field(
        default="low",
        description="Risk level of the request.",
    )
    approval_required: bool = Field(
        default=False,
        description="Whether human approval is required.",
    )
    approval_id: str | None = Field(
        default=None,
        description="Approval request ID for high-risk actions.",
    )
