"""人工审批 API 路由。"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session

from ecom_agent.commerce.approval_models import ApprovalRecord
from ecom_agent.commerce.approval_repository import ApprovalRepository
from ecom_agent.commerce.database import get_session
from ecom_agent.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalResponse,
)
from ecom_agent.settings import get_settings

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
)

logger = logging.getLogger(__name__)


def require_approval_reviewer(
    reviewer_id: Annotated[
        str | None,
        Header(alias="X-Reviewer-ID"),
    ] = None,
    reviewer_role: Annotated[
        str | None,
        Header(alias="X-Reviewer-Role"),
    ] = None,
) -> str:
    """校验审批审核者身份和角色。"""

    allowed_reviewer_ids = {
        item.strip() for item in get_settings().approval_reviewer_ids.split(",") if item.strip()
    }

    if reviewer_id not in allowed_reviewer_ids:
        raise HTTPException(
            status_code=403,
            detail="Reviewer is not authorized.",
        )

    if reviewer_role not in {"reviewer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Reviewer role is not allowed.",
        )

    return reviewer_id


def _to_response(approval: ApprovalRecord) -> ApprovalResponse:
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
    session: Annotated[Session, Depends(get_session)],
) -> ApprovalResponse:
    """返回一个审批请求。"""

    repository = ApprovalRepository(session)
    approval = repository.get(approval_id)

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
    reviewer_id: Annotated[
        str,
        Depends(require_approval_reviewer),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> ApprovalResponse:
    """批准或拒绝一个待处理请求。"""

    repository = ApprovalRepository(session)
    approval = repository.decide(
        approval_id=approval_id,
        approved=request.approved,
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    logger.info(
        "approval_decision approval_id=%s reviewer_id=%s approved=%s status=%s",
        approval_id,
        reviewer_id,
        request.approved,
        approval.status,
    )

    return _to_response(approval)
