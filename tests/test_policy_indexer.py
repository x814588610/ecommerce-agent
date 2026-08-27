"""测试售后政策索引器。"""

from collections.abc import Sequence

from ecom_agent.retrieval.policy_documents import (
    PolicyDocument,
    get_default_policy_documents,
)
from ecom_agent.retrieval.policy_indexer import index_policies


class FakePolicyVectorStore:
    """记录收到的政策文档。"""

    def __init__(self) -> None:
        self.documents: list[PolicyDocument] = []

    def upsert_documents(
        self,
        documents: Sequence[PolicyDocument],
    ) -> int:
        """保存政策文档并返回数量。"""

        self.documents = list(documents)
        return len(self.documents)


def test_index_policies_uses_default_documents() -> None:
    """未传入文档时应该索引默认政策。"""

    vector_store = FakePolicyVectorStore()

    count = index_policies(vector_store)

    assert count == 4
    assert vector_store.documents == get_default_policy_documents()
    assert vector_store.documents[0].policy_id == "return-policy"


def test_index_policies_accepts_custom_documents() -> None:
    """索引器应该支持传入自定义政策。"""

    vector_store = FakePolicyVectorStore()
    documents = [
        PolicyDocument(
            policy_id="custom-policy",
            title="自定义政策",
            content="这是测试政策。",
        )
    ]

    count = index_policies(vector_store, documents)

    assert count == 1
    assert vector_store.documents == documents