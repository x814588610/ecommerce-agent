"""Tests for human approval API routes."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from ecom_agent.agent.approval import ApprovalStore
from ecom_agent.api.chat import get_agent_model, get_approval_store
from ecom_agent.api.main import app
from ecom_agent.commerce.database import get_session


@contextmanager
def create_test_client() -> Iterator[tuple[TestClient, ApprovalStore]]:
    """Create an API client with an isolated approval store."""

    test_store = ApprovalStore()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    def override_get_session() -> Iterator[Session]:
        with Session(test_engine) as session:
            yield session

    def override_get_agent_model() -> Callable[[], object]:
        return object

    def override_get_approval_store() -> ApprovalStore:
        return test_store

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_agent_model] = override_get_agent_model
    app.dependency_overrides[get_approval_store] = (
        override_get_approval_store
    )

    client = TestClient(app)

    try:
        yield client, test_store
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_high_risk_chat_creates_queryable_approval() -> None:
    """A high-risk chat request should create a pending approval."""

    with create_test_client() as (client, _store):
        chat_response = client.post(
            "/chat",
            json={
                "message": "我要申请退款",
                "session_id": "session-001",
                "user_id": "user-001",
            },
        )
        approval_id = chat_response.json()["approval_id"]
        approval_response = client.get(
            f"/approvals/{approval_id}"
        )

    assert chat_response.status_code == 200
    assert approval_response.status_code == 200
    assert approval_response.json() == {
        "approval_id": approval_id,
        "session_id": "session-001",
        "user_id": "user-001",
        "action": "我要申请退款",
        "status": "pending",
    }


@pytest.mark.parametrize(
    ("approved", "expected_status"),
    [
        (True, "approved"),
        (False, "rejected"),
    ],
)
def test_decide_approval(
    approved: bool,
    expected_status: str,
) -> None:
    """A reviewer should be able to approve or reject a request."""

    with create_test_client() as (client, store):
        approval = store.create(
            session_id="session-001",
            user_id="user-001",
            action="取消订单",
        )

        response = client.post(
            f"/approvals/{approval.approval_id}/decision",
            json={"approved": approved},
        )

    assert response.status_code == 200
    assert response.json()["status"] == expected_status


def test_missing_approval_returns_404() -> None:
    """Unknown approval IDs should return HTTP 404."""

    with create_test_client() as (client, _store):
        get_response = client.get(
            "/approvals/approval-not-found"
        )
        decision_response = client.post(
            "/approvals/approval-not-found/decision",
            json={"approved": True},
        )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Approval request not found."
    }
    assert decision_response.status_code == 404


def test_decision_requires_approved_field() -> None:
    """A decision without an approved value should be rejected."""

    with create_test_client() as (client, store):
        approval = store.create(
            session_id="session-001",
            user_id="user-001",
            action="修改收货地址",
        )

        response = client.post(
            f"/approvals/{approval.approval_id}/decision",
            json={},
        )

    assert response.status_code == 422
    assert approval.status == "pending"