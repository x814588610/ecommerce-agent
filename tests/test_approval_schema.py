"""Tests for approval API schemas."""

import pytest
from pydantic import ValidationError

from ecom_agent.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalResponse,
)


def test_approval_decision_accepts_boolean() -> None:
    """A reviewer should be able to approve or reject a request."""

    approved = ApprovalDecisionRequest(approved=True)
    rejected = ApprovalDecisionRequest(approved=False)

    assert approved.approved is True
    assert rejected.approved is False


def test_approval_decision_requires_value() -> None:
    """An approval decision must contain the approved field."""

    with pytest.raises(ValidationError):
        ApprovalDecisionRequest()


def test_approval_response_accepts_pending_status() -> None:
    """A valid pending approval response should be created."""

    response = ApprovalResponse(
        approval_id="approval-001",
        session_id="session-001",
        user_id="user-001",
        action="申请退款",
        status="pending",
    )

    assert response.approval_id == "approval-001"
    assert response.status == "pending"


def test_approval_response_rejects_invalid_status() -> None:
    """An unknown approval status should fail validation."""

    with pytest.raises(ValidationError):
        ApprovalResponse(
            approval_id="approval-001",
            session_id="session-001",
            user_id="user-001",
            action="申请退款",
            status="unknown",
        )