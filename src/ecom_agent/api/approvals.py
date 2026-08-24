"""Human approval API routes."""

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
    """Convert an approval record into an API response."""

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
    """Return one approval request."""

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
    """Approve or reject one pending request."""

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