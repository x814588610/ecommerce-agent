"""In-memory conversation history."""

from langchain_core.messages import AnyMessage


class ConversationMemory:
    """Store conversation messages by session ID."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[AnyMessage]] = {}

    def load(self, session_id: str) -> list[AnyMessage]:
        """Return a copy of the messages in one session."""

        return list(self._sessions.get(session_id, []))

    def save(self, session_id: str, messages: list[AnyMessage]) -> None:
        """Save a copy of the messages for one session."""

        self._sessions[session_id] = list(messages)

    def clear(self, session_id: str) -> None:
        """Delete one conversation session."""

        self._sessions.pop(session_id, None)