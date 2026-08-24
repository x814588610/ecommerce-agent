"""Approval request and response schemas."""

from pydantic import BaseModel, Field

from ecom_agent.agent.approval import ApprovalStatus


class ApprovalDecisionRequest(BaseModel):
    """Decision submitted by a human reviewer."""

    approved: bool = Field(
        description="Whether the approval request is approved.",
    )


class ApprovalResponse(BaseModel):
    """Approval request returned by the API."""

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