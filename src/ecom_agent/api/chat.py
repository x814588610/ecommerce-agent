"""聊天 API 路由。"""

import logging
from collections.abc import Callable
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from sqlmodel import Session

from ecom_agent.agent.graph import build_commerce_graph
from ecom_agent.agent.memory import ConversationMemory
from ecom_agent.agent.policies import assess_risk
from ecom_agent.agent.registry import create_commerce_tools
from ecom_agent.agent.state import AgentState, create_initial_state
from ecom_agent.commerce.approval_models import ApprovalRecord
from ecom_agent.commerce.approval_repository import ApprovalRepository
from ecom_agent.commerce.database import get_session
from ecom_agent.llm.factory import create_chat_model
from ecom_agent.retrieval.factory import (
    get_policy_vector_store,
    get_product_vector_store,
)
from ecom_agent.retrieval.policy_vector_store import PolicyVectorStore
from ecom_agent.retrieval.vector_store import ProductVectorStore
from ecom_agent.schemas.message import ChatRequest, ChatResponse

ModelFactory = Callable[[], BaseChatModel]
ProductVectorStoreFactory = Callable[[], ProductVectorStore]
PolicyVectorStoreFactory = Callable[[], PolicyVectorStore]
logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

conversation_memory = ConversationMemory()


def get_agent_model() -> ModelFactory:
    """返回用于创建 Agent 模型的工厂函数。"""

    return create_chat_model


def get_product_vector_store_factory() -> ProductVectorStoreFactory:
    """返回延迟创建商品向量存储的工厂函数。"""

    return get_product_vector_store


def get_policy_vector_store_factory() -> PolicyVectorStoreFactory:
    """返回延迟创建售后政策向量存储的工厂函数。"""

    return get_policy_vector_store


def get_conversation_memory() -> ConversationMemory:
    """返回会话记忆服务。"""

    return conversation_memory


def _build_agent_state(
    request: ChatRequest,
    memory: ConversationMemory,
) -> AgentState:
    """根据历史消息和当前用户消息构建 Agent 状态。"""

    state = create_initial_state(
        user_message=request.message,
        session_id=request.session_id,
        user_id=request.user_id,
    )

    messages = memory.load(request.session_id)
    messages.append(HumanMessage(content=request.message))
    state["messages"] = messages

    return state


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    session: Annotated[Session, Depends(get_session)],
    model_factory: Annotated[ModelFactory, Depends(get_agent_model)],
    memory: Annotated[
        ConversationMemory,
        Depends(get_conversation_memory),
    ],
    product_store_factory: Annotated[
        ProductVectorStoreFactory,
        Depends(get_product_vector_store_factory),
    ],
    policy_store_factory: Annotated[
        PolicyVectorStoreFactory,
        Depends(get_policy_vector_store_factory),
    ],
) -> ChatResponse:
    """使用电商 Agent 回答一条用户消息。"""

    risk_level, approval_required = assess_risk(request.message)

    if approval_required:
        approval_repository = ApprovalRepository(session)

        approval = approval_repository.add(
            ApprovalRecord(
                approval_id=f"approval-{uuid4().hex}",
                session_id=request.session_id,
                user_id=request.user_id,
                action=request.message,
            )
        )

        return ChatResponse(
            answer="这个操作需要人工审批，我不能直接执行。",
            session_id=request.session_id,
            step_count=0,
            risk_level=risk_level,
            approval_required=True,
            approval_id=approval.approval_id,
        )

    try:
        model = model_factory()
        vector_store = product_store_factory()
        policy_vector_store = policy_store_factory()
        tools = create_commerce_tools(
            session,
            vector_store,
            policy_vector_store,
            user_id=request.user_id,
        )
        graph = build_commerce_graph(model, tools)
        result = graph.invoke(
            _build_agent_state(
                request=request,
                memory=memory,
            )
        )
    except ValueError as exc:
        logger.exception("Agent configuration error.")
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Agent request failed.")
        raise HTTPException(
            status_code=500,
            detail="Agent request failed.",
        ) from exc

    answer = result.get("answer", "")
    step_count = result.get("step_count", 0)
    messages = result.get("messages", [])

    if not isinstance(answer, str) or not answer:
        raise HTTPException(
            status_code=500,
            detail="Agent did not return an answer.",
        )

    if not isinstance(messages, list):
        raise HTTPException(
            status_code=500,
            detail="Agent did not return valid messages.",
        )

    memory.save(request.session_id, messages)

    return ChatResponse(
        answer=answer,
        session_id=request.session_id,
        step_count=step_count,
        risk_level=risk_level,
        approval_required=approval_required,
        approval_id=None,
    )
