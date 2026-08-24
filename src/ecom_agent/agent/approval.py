"""Human approval records for high-risk actions."""

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

ApprovalStatus = Literal["pending", "approved", "rejected"]


@dataclass
class ApprovalRequest:
    """A human approval request."""

    approval_id: str
    session_id: str
    user_id: str
    action: str
    status: ApprovalStatus = "pending"


class ApprovalStore:
    """Store approval requests in memory."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create(
        self,
        session_id: str,
        user_id: str,
        action: str,
    ) -> ApprovalRequest:
        """Create a pending approval request."""

        approval = ApprovalRequest(
            approval_id=f"approval-{uuid4().hex}",
            session_id=session_id,
            user_id=user_id,
            action=action,
        )
        self._requests[approval.approval_id] = approval
        return approval

    def get(self, approval_id: str) -> ApprovalRequest | None:
        """Find an approval request by ID."""

        return self._requests.get(approval_id)

    def decide(
        self,
        approval_id: str,
        approved: bool,
    ) -> ApprovalRequest | None:
        """Approve or reject a pending request."""

        approval = self.get(approval_id)

        if approval is None:
            return None

        if approval.status != "pending":
            return approval

        approval.status = "approved" if approved else "rejected"
        return approval