"""高风险操作的人工审批记录。"""

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

ApprovalStatus = Literal["pending", "approved", "rejected"]


@dataclass
class ApprovalRequest:
    """人工审批请求。"""

    approval_id: str
    session_id: str
    user_id: str
    action: str
    status: ApprovalStatus = "pending"


class ApprovalStore:
    """在内存中保存审批请求。"""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create(
        self,
        session_id: str,
        user_id: str,
        action: str,
    ) -> ApprovalRequest:
        """创建一个待处理的审批请求。"""

        approval = ApprovalRequest(
            approval_id=f"approval-{uuid4().hex}",
            session_id=session_id,
            user_id=user_id,
            action=action,
        )
        self._requests[approval.approval_id] = approval
        return approval

    def get(self, approval_id: str) -> ApprovalRequest | None:
        """根据 ID 查找审批请求。"""

        return self._requests.get(approval_id)

    def decide(
        self,
        approval_id: str,
        approved: bool,
    ) -> ApprovalRequest | None:
        """批准或拒绝一个待处理的请求。"""

        approval = self.get(approval_id)

        if approval is None:
            return None

        if approval.status != "pending":
            return approval

        approval.status = "approved" if approved else "rejected"
        return approval
