"""审批记录数据库操作。"""

from sqlmodel import Session, select

from ecom_agent.commerce.approval_models import ApprovalRecord


class ApprovalRepository:
    """提供审批记录的保存、查询和决定功能。"""

    def __init__(self, session: Session) -> None:
        """保存数据库会话。"""

        self.session = session

    def add(self, approval: ApprovalRecord) -> ApprovalRecord:
        """保存一条审批记录。"""

        try:
            self.session.add(approval)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(approval)
        return approval

    def get(self, approval_id: str) -> ApprovalRecord | None:
        """根据审批 ID 查询记录。"""

        statement = select(ApprovalRecord).where(
            ApprovalRecord.approval_id == approval_id,
        )
        return self.session.exec(statement).first()

    def decide(
        self,
        approval_id: str,
        approved: bool,
    ) -> ApprovalRecord | None:
        """更新审批结果，已完成的审批不能重复修改。"""

        approval = self.get(approval_id)

        if approval is None:
            return None

        if approval.status != "pending":
            return approval

        approval.status = "approved" if approved else "rejected"

        try:
            self.session.add(approval)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(approval)
        return approval
