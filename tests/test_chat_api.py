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
from ecom_agent.retrieval.factory import (
    get_policy_vector_store,
    get_product_vector_store,
)
from ecom_agent.retrieval.policy_vector_store import PolicySearchResult
from ecom_agent.retrieval.vector_store import ProductSearchResult


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

class FakeVectorStore:
    """模拟商品向量存储。"""

    def search(
        self,
        query: str,
        limit: int = 5,
        only_in_stock: bool = True,
    ) -> list[ProductSearchResult]:
        """返回固定的商品语义搜索结果。"""

        return [
            ProductSearchResult(
                product_id="phone-001",
                score=0.93,
                payload={
                    "product_id": "phone-001",
                },
            )
        ]

class FakePolicyVectorStore:
    """模拟售后政策向量存储。"""

    def __init__(
        self,
        results: list[PolicySearchResult] | None = None,
    ) -> None:
        """保存测试用的政策结果。"""

        self.results = results or []
        self.calls: list[tuple[str, int]] = []

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[PolicySearchResult]:
        """记录搜索参数并返回固定结果。"""

        self.calls.append((query, limit))
        return self.results[:limit]

def create_policy_result() -> PolicySearchResult:
    """创建测试用的售后政策结果。"""

    return PolicySearchResult(
        policy_id="refund-policy",
        score=0.94,
        payload={
            "title": "退款政策",
            "content": "退货审核通过后，原路退款通常需要 3 到 7 个工作日到账。",
            "source": "本地售后政策",
        },
    )


@contextmanager
def create_test_client(
    model: FakeModel,
    vector_store: FakeVectorStore | None = None,
    policy_vector_store: FakePolicyVectorStore | None = None,
) -> Iterator[TestClient]:
    """Create an API client with isolated database and fake model."""


    if vector_store is None:
        vector_store = FakeVectorStore()

    if policy_vector_store is None:
        policy_vector_store = FakePolicyVectorStore()

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

    def override_get_product_vector_store() -> FakeVectorStore:
        return vector_store
    
    def override_get_policy_vector_store() -> FakePolicyVectorStore:
        return policy_vector_store
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_agent_model] = override_get_agent_model
    app.dependency_overrides[get_conversation_memory] = (
        override_get_conversation_memory
    )
    app.dependency_overrides[get_approval_store] = (
        override_get_approval_store
    )
    app.dependency_overrides[get_product_vector_store] = (
        override_get_product_vector_store
    )
    app.dependency_overrides[get_policy_vector_store] = (
        override_get_policy_vector_store
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



def test_chat_executes_semantic_product_tool() -> None:
    """聊天 Agent 应该能够执行商品语义搜索工具。"""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "semantic_search_products",
                        "args": {
                            "query": "适合学生学习的手机",
                            "limit": 3,
                        },
                        "id": "semantic-call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="我找到了一部适合学生学习的手机，价格是 1999 元。"
            ),
        ]
    )
    vector_store = FakeVectorStore()

    with create_test_client(model, vector_store) as client:
        response = client.post(
            "/chat",
            json={
                "message": "推荐适合学生学习的手机",
                "session_id": "semantic-session",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "我找到了一部适合学生学习的手机，价格是 1999 元。",
        "session_id": "semantic-session",
        "step_count": 2,
        "risk_level": "low",
        "approval_required": False,
        "approval_id": None,
    }
    assert len(model.calls) == 2
    assert model.calls[1][-1].type == "tool"
    assert "phone-001" in model.calls[1][-1].content
    assert "0.93" in model.calls[1][-1].content

def test_chat_executes_policy_tool() -> None:
    """聊天 Agent 应该能够执行售后政策搜索工具。"""

    model = FakeModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_policy",
                        "args": {
                            "query": "退款通常多久到账？",
                            "limit": 3,
                        },
                        "id": "policy-call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="退款审核通过后，通常需要 3 到 7 个工作日到账。"
            ),
        ]
    )
    policy_vector_store = FakePolicyVectorStore(
        results=[create_policy_result()]
    )

    with create_test_client(
        model,
        policy_vector_store=policy_vector_store,
    ) as client:
        response = client.post(
            "/chat",
            json={
                "message": "退款通常多久到账？",
                "session_id": "policy-session",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "退款审核通过后，通常需要 3 到 7 个工作日到账。",
        "session_id": "policy-session",
        "step_count": 2,
        "risk_level": "low",
        "approval_required": False,
        "approval_id": None,
    }
    assert len(model.calls) == 2
    assert model.calls[1][-1].type == "tool"
    assert "退款政策" in model.calls[1][-1].content
    assert "3 到 7 个工作日" in model.calls[1][-1].content
    assert policy_vector_store.calls == [
        ("退款通常多久到账？", 3)
    ]