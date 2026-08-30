"""审批请求和响应模型。"""
from typing import Literal

from pydantic import BaseModel, Field

ApprovalStatus = Literal["pending", "approved", "rejected"]
class ApprovalDecisionRequest(BaseModel):
    """人工审核者提交的决定。"""

    approved: bool = Field(
        description="Whether the approval request is approved.",
    )


class ApprovalResponse(BaseModel):
    """API 返回的审批请求。"""

    approval_id: str = Field(
        min_length=1,
        description="Approval request ID.",
    )
    session_id: str = Field(
        min_length=1,
        description="Conversation session ID.",
    )
    user_id: str = Field(
        min_length=1,
        description="User ID.",
    )
    action: str = Field(
        min_length=1,
        description="High-risk action awaiting review.",
    )
    status: ApprovalStatus = Field(
        description="Current approval status.",
    )
