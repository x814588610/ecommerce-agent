"""Tests for human approval records."""

from ecom_agent.agent.approval import ApprovalStore


def test_create_approval_request() -> None:
    """A new approval request should be pending."""

    store = ApprovalStore()

    approval = store.create(
        session_id="session-001",
        user_id="user-001",
        action="申请退款",
    )

    assert approval.approval_id.startswith("approval-")
    assert approval.session_id == "session-001"
    assert approval.user_id == "user-001"
    assert approval.action == "申请退款"
    assert approval.status == "pending"
    assert store.get(approval.approval_id) is approval


def test_approve_pending_request() -> None:
    """A pending request should become approved."""

    store = ApprovalStore()
    approval = store.create(
        session_id="session-001",
        user_id="user-001",
        action="取消订单",
    )

    result = store.decide(approval.approval_id, approved=True)

    assert result is approval
    assert result.status == "approved"


def test_reject_pending_request() -> None:
    """A pending request should become rejected."""

    store = ApprovalStore()
    approval = store.create(
        session_id="session-001",
        user_id="user-001",
        action="修改收货地址",
    )

    result = store.decide(approval.approval_id, approved=False)

    assert result is approval
    assert result.status == "rejected"


def test_missing_approval_returns_none() -> None:
    """An unknown approval ID should return None."""

    store = ApprovalStore()

    assert store.get("approval-not-found") is None
    assert store.decide("approval-not-found", approved=True) is None


def test_finished_approval_cannot_be_changed() -> None:
    """An approved request should not be changed to rejected."""

    store = ApprovalStore()
    approval = store.create(
        session_id="session-001",
        user_id="user-001",
        action="申请退款",
    )

    store.decide(approval.approval_id, approved=True)
    result = store.decide(approval.approval_id, approved=False)

    assert result is approval
    assert result.status == "approved"