"""Tests for the commerce agent state."""

from ecom_agent.agent.state import create_initial_state


def test_create_initial_state_initializes_all_fields() -> None:
    """A new state should contain all expected default values."""

    state = create_initial_state(
        user_message="我想找一台学习用的电脑",
        session_id="session-001",
        user_id="user-001",
    )

    assert state["messages"] == [
        {
            "role": "user",
            "content": "我想找一台学习用的电脑",
        }
    ]
    assert state["user_id"] == "user-001"
    assert state["session_id"] == "session-001"
    assert state["intent"] == ""
    assert state["search_query"] == ""
    assert state["tool_results"] == []
    assert state["answer"] == ""
    assert state["risk_level"] == "low"
    assert state["approval_required"] is False
    assert state["error"] is None
    assert state["step_count"] == 0


def test_create_initial_state_uses_independent_lists() -> None:
    """Different conversations should not share mutable state."""

    first_state = create_initial_state("第一个问题")
    second_state = create_initial_state("第二个问题")

    first_state["tool_results"].append({"product_id": "phone-001"})

    assert first_state["tool_results"] == [{"product_id": "phone-001"}]
    assert second_state["tool_results"] == []