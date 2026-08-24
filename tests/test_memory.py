"""Tests for conversation memory."""

from langchain_core.messages import AIMessage, HumanMessage

from ecom_agent.agent.memory import ConversationMemory


def test_unknown_session_returns_empty_history() -> None:
    """A new session should have no messages."""

    memory = ConversationMemory()

    assert memory.load("session-001") == []


def test_save_and_load_conversation_messages() -> None:
    """Saved messages should be returned in their original order."""

    memory = ConversationMemory()
    messages = [
        HumanMessage(content="我想买一台电脑"),
        AIMessage(content="可以，我来帮你查询。"),
    ]

    memory.save("session-001", messages)

    loaded_messages = memory.load("session-001")

    assert loaded_messages == messages
    assert loaded_messages is not messages


def test_sessions_are_isolated_and_can_be_cleared() -> None:
    """Different sessions should not share messages."""

    memory = ConversationMemory()

    memory.save(
        "session-001",
        [HumanMessage(content="第一个会话")],
    )
    memory.save(
        "session-002",
        [HumanMessage(content="第二个会话")],
    )

    memory.clear("session-001")

    assert memory.load("session-001") == []
    assert memory.load("session-002")[0].content == "第二个会话"