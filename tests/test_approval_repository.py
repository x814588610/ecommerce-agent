"""审批记录仓储测试。"""

from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from ecom_agent.commerce.approval_models import ApprovalRecord
from ecom_agent.commerce.approval_repository import ApprovalRepository


def create_test_session() -> Session:
    """创建独立的内存数据库会话。"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def create_approval(
    session: Session,
    approval_id: str = "approval-001",
) -> ApprovalRecord:
    """创建测试审批记录。"""

    repository = ApprovalRepository(session)
    approval = ApprovalRecord(
        approval_id=approval_id,
        session_id="session-001",
        user_id="user-001",
        action="申请退款",
    )
    return repository.add(approval)


def test_add_and_get_approval() -> None:
    """审批记录应该能够保存和查询。"""

    with create_test_session() as session:
        repository = ApprovalRepository(session)
        approval = create_approval(session)

        result = repository.get(approval.approval_id)

    assert result is not None
    assert result.approval_id == "approval-001"
    assert result.session_id == "session-001"
    assert result.user_id == "user-001"
    assert result.action == "申请退款"
    assert result.status == "pending"
    assert result.created_at is not None


def test_decide_pending_approval() -> None:
    """待审批记录应该能够变更状态。"""

    with create_test_session() as session:
        repository = ApprovalRepository(session)
        approval = create_approval(session)

        result = repository.decide(
            approval_id=approval.approval_id,
            approved=True,
        )

    assert result is not None
    assert result.status == "approved"


def test_finished_approval_is_idempotent() -> None:
    """已经完成的审批不能再次改变。"""

    with create_test_session() as session:
        repository = ApprovalRepository(session)
        approval = create_approval(session)

        repository.decide(approval.approval_id, approved=True)
        result = repository.decide(approval.approval_id, approved=False)

    assert result is not None
    assert result.status == "approved"


def test_missing_approval_returns_none() -> None:
    """不存在的审批记录应该返回 None。"""

    with create_test_session() as session:
        repository = ApprovalRepository(session)

        result = repository.get("approval-not-found")
        decision = repository.decide(
            approval_id="approval-not-found",
            approved=True,
        )

    assert result is None
    assert decision is None


def test_approval_survives_new_database_session(
    tmp_path: Path,
) -> None:
    """审批记录应该能够在新的数据库会话中继续查询。"""

    database_path = tmp_path / "approvals.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    first_engine = create_engine(database_url)
    SQLModel.metadata.create_all(first_engine)

    with Session(first_engine) as session:
        repository = ApprovalRepository(session)
        repository.add(
            ApprovalRecord(
                approval_id="approval-persistent-001",
                session_id="persist-session",
                user_id="user-001",
                action="申请退款",
                status="approved",
            )
        )

    first_engine.dispose()

    second_engine = create_engine(database_url)

    with Session(second_engine) as session:
        repository = ApprovalRepository(session)
        result = repository.get("approval-persistent-001")

    second_engine.dispose()

    assert result is not None
    assert result.session_id == "persist-session"
    assert result.user_id == "user-001"
    assert result.status == "approved"
