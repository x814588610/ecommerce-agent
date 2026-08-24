"""Tests for the chat API."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from decimal import Decimal

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.agent.approval import ApprovalStore
from ecom_agent.agent.memory import ConversationMemory
from ecom_agent.api.chat import (
    get_agent_model,
    get_approval_store,
    get_conversation_memory,
)
from ecom_agent.api.main import app
from ecom_agent.commerce.database import get_session
from ecom_agent.commerce.models import ProductRecord
from ecom_agent.commerce.repository import ProductRepository


class FakeModel:
    """A fake model that returns predefined responses."""

    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = list(responses)
        self.calls: list[list[object]] = []

    def bind_tools(self, tools: list[object]) -> "FakeModel":
        """Accept the tools required by the graph."""

        return self

    def invoke(self, messages: list[object]) -> AIMessage:
        """Return the next predefined response."""

        self.calls.append(messages)
        return self.responses.pop(0)


@contextmanager
def create_test_client(model: FakeModel) -> Iterator[TestClient]:
    """Create an API client with isolated database and fake model."""
    test_approval_store = ApprovalStore()
    test_memory = ConversationMemory()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        ProductRepository(session).add(
            ProductRecord(
                product_id="phone-001",
                name="学习手机",
                category="手机",
                brand="星河",
                description="适合学生学习和日常使用。",
                price=Decimal("1999.00"),
                stock=10,
            )
        )

    def override_get_session() -> Iterator[Session]:
        with Session(test_engine) as session:
            yield session

    def override_get_agent_model() -> Callable[[], FakeModel]:
        return lambda: model

    def override_get_approval_store() -> ApprovalStore:
        return test_approval_store

    def override_get_conversation_memory() -> ConversationMemory:
        return test_memory
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_agent_model] = override_get_agent_model
    app.dependency_overrides[get_conversation_memory] = (
        override_get_conversation_memory
    )
    app.dependency_overrides[get_approval_store] = (
        override_get_approval_store
    )

    client = TestClient(app)

    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_chat_returns_model_answer() -> None:
    """The chat endpoint should return a direct model answer."""

    model = FakeModel(
        [
            AIMessage(content="推荐学习手机。"),
        ]
    )

    with create_test_client(model) as client:
        response = client.post(
            "/chat",
            json={"message": "推荐一部学习用的手机"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "推荐学习手机。",
        "session_id": "default-session",
        "step_count": 1,
        "risk_level": "low",
        "approval_required": False,
        "approval_id": None,
    }
    assert len(model.calls) == 1


def test_chat_executes_product_tool() -> None:
    """The chat endpoint should execute a requested product tool."""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_products",
                        "args": {"query": "手机"},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="找到一部有库存的学习手机，价格是 1999 元。"),
        ]
    )

    with create_test_client(model) as client:
        response = client.post(
            "/chat",
            json={
                "message": "帮我找一部有库存的手机",
                "session_id": "session-001",
                "user_id": "user-001",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "找到一部有库存的学习手机，价格是 1999 元。",
        "session_id": "session-001",
        "step_count": 2,
        "risk_level": "low",
        "approval_required": False,
        "approval_id": None,
    }
    assert len(model.calls) == 2
    assert model.calls[1][-1].type == "tool"


def test_chat_rejects_empty_message() -> None:
    """The chat endpoint should reject an empty message."""

    model = FakeModel([AIMessage(content="不会执行")])

    with create_test_client(model) as client:
        response = client.post(
            "/chat",
            json={"message": ""},
        )

    assert response.status_code == 422
    assert len(model.calls) == 0


def test_chat_reuses_memory_for_same_session() -> None:
    """The second request should include the first conversation turn."""

    model = FakeModel(
        [
            AIMessage(content="第一轮回答：推荐学习手机。"),
            AIMessage(content="第二轮回答：它的价格是 1999 元。"),
        ]
    )

    with create_test_client(model) as client:
        first_response = client.post(
            "/chat",
            json={
                "message": "我想找一部学习用的手机",
                "session_id": "session-memory",
            },
        )
        second_response = client.post(
            "/chat",
            json={
                "message": "它的价格是多少？",
                "session_id": "session-memory",
            },
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["answer"] == (
        "第二轮回答：它的价格是 1999 元。"
    )

    second_call_contents = [
        getattr(message, "content", "")
        for message in model.calls[1]
    ]

    assert "我想找一部学习用的手机" in second_call_contents
    assert "第一轮回答：推荐学习手机。" in second_call_contents
    assert second_call_contents[-1] == "它的价格是多少？"



def test_chat_blocks_high_risk_action_before_model() -> None:
    """High-risk actions should require approval before model execution."""

    model = FakeModel(
        [
            AIMessage(content="这段回答不应该被调用。"),
        ]
    )

    with create_test_client(model) as client:
        response = client.post(
            "/chat",
            json={
                "message": "我要申请退款",
                "session_id": "risk-session",
            },
        )

    data = response.json()

    assert response.status_code == 200
    assert data["answer"] == "这个操作需要人工审批，我不能直接执行。"
    assert data["session_id"] == "risk-session"
    assert data["step_count"] == 0
    assert data["risk_level"] == "high"
    assert data["approval_required"] is True
    assert data["approval_id"].startswith("approval-")
    assert len(model.calls) == 0