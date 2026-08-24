"""Tests for chat request and response schemas."""

import pytest
from pydantic import ValidationError

from ecom_agent.schemas.message import ChatRequest, ChatResponse


def test_chat_request_uses_default_values() -> None:
    """A chat request should provide default session and user IDs."""

    request = ChatRequest(message="我想买一台电脑")

    assert request.message == "我想买一台电脑"
    assert request.session_id == "default-session"
    assert request.user_id == "anonymous"


def test_chat_request_accepts_custom_session_and_user() -> None:
    """A chat request should preserve custom identifiers."""

    request = ChatRequest(
        message="查询商品库存",
        session_id="session-001",
        user_id="user-001",
    )

    assert request.session_id == "session-001"
    assert request.user_id == "user-001"


def test_chat_request_rejects_empty_message() -> None:
    """An empty user message should fail validation."""

    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_chat_request_rejects_overlong_message() -> None:
    """A message longer than 2000 characters should fail validation."""

    with pytest.raises(ValidationError):
        ChatRequest(message="a" * 2001)


def test_chat_response_contains_agent_result() -> None:
    """A chat response should contain the answer and execution count."""

    response = ChatResponse(
        answer="推荐轻薄办公本。",
        session_id="session-001",
        step_count=2,
    )

    assert response.answer == "推荐轻薄办公本。"
    assert response.session_id == "session-001"
    assert response.step_count == 2