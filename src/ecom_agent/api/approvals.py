"""人工审批 API 路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ecom_agent.agent.approval import (
    ApprovalRequest,
    ApprovalStore,
)
from ecom_agent.api.chat import get_approval_store
from ecom_agent.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalResponse,
)

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
)


def _to_response(approval: ApprovalRequest) -> ApprovalResponse:
    """将审批记录转换为 API 响应。"""

    return ApprovalResponse(
        approval_id=approval.approval_id,
        session_id=approval.session_id,
        user_id=approval.user_id,
        action=approval.action,
        status=approval.status,
    )


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: str,
    store: Annotated[ApprovalStore, Depends(get_approval_store)],
) -> ApprovalResponse:
    """返回一个审批请求。"""

    approval = store.get(approval_id)

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    return _to_response(approval)


@router.post(
    "/{approval_id}/decision",
    response_model=ApprovalResponse,
)
def decide_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
    store: Annotated[ApprovalStore, Depends(get_approval_store)],
) -> ApprovalResponse:
    """批准或拒绝一个待处理请求。"""

    approval = store.decide(
        approval_id=approval_id,
        approved=request.approved,
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    return _to_response(approval)
