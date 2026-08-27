"""内存中的会话历史。"""

from langchain_core.messages import AnyMessage


class ConversationMemory:
    """按会话 ID 保存对话消息。"""

    def __init__(self) -> None:
        self._sessions: dict[str, list[AnyMessage]] = {}

    def load(self, session_id: str) -> list[AnyMessage]:
        """返回某个会话中消息的副本。"""

        return list(self._sessions.get(session_id, []))

    def save(self, session_id: str, messages: list[AnyMessage]) -> None:
        """保存某个会话的消息副本。"""

        self._sessions[session_id] = list(messages)

    def clear(self, session_id: str) -> None:
        """删除一个会话。"""

        self._sessions.pop(session_id, None)
