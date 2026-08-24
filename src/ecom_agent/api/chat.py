"""Chat API routes."""

import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from sqlmodel import Session

from ecom_agent.agent.approval import ApprovalStore
from ecom_agent.agent.graph import build_commerce_graph
from ecom_agent.agent.memory import ConversationMemory
from ecom_agent.agent.policies import assess_risk
from ecom_agent.agent.registry import create_commerce_tools
from ecom_agent.agent.state import AgentState, create_initial_state
from ecom_agent.commerce.database import get_session
from ecom_agent.llm.factory import create_chat_model
from ecom_agent.schemas.message import ChatRequest, ChatResponse

ModelFactory = Callable[[], BaseChatModel]
logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

conversation_memory = ConversationMemory()
approval_store = ApprovalStore()


def get_agent_model() -> ModelFactory:
    """Return a factory that creates the agent model."""

    return create_chat_model


def get_approval_store() -> ApprovalStore:
    """Return the approval store."""

    return approval_store


def get_conversation_memory() -> ConversationMemory:
    """Return the conversation memory service."""

    return conversation_memory


def _build_agent_state(
    request: ChatRequest,
    memory: ConversationMemory,
) -> AgentState:
    """Build agent state from history and the current user message."""

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
    approval_store: Annotated[
        ApprovalStore,
        Depends(get_approval_store),
    ],
) -> ChatResponse:
    """Answer one user message with the commerce agent."""

    risk_level, approval_required = assess_risk(request.message)

    if approval_required:
        approval = approval_store.create(
            session_id=request.session_id,
            user_id=request.user_id,
            action=request.message,
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
        tools = create_commerce_tools(session)
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