"""审批记录数据库模型。"""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc)


class ApprovalRecord(SQLModel, table=True):
    """保存人工审批请求。"""

    __tablename__ = "approvals"

    approval_id: str = Field(
        primary_key=True,
        max_length=100,
    )
    session_id: str = Field(
        index=True,
        max_length=100,
    )
    user_id: str = Field(
        index=True,
        max_length=100,
    )
    action: str = Field(
        max_length=200,
    )
    status: str = Field(
        default="pending",
        index=True,
        max_length=20,
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
    )
