"""测试售后政策向量存储。"""

from collections.abc import Sequence

import pytest
from qdrant_client import QdrantClient

from ecom_agent.retrieval.policy_documents import PolicyDocument
from ecom_agent.retrieval.policy_vector_store import PolicyVectorStore


class FakePolicyEmbedding:
    """用于测试的固定向量模型。"""

    dimension = 2

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """将政策文本转换为固定向量。"""

        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """将用户问题转换为固定向量。"""

        return self._embed(text)

    @staticmethod
    def _embed(text: str) -> list[float]:
        """根据政策关键词返回不同方向的向量。"""

        if "退货" in text or "退款" in text:
            return [1.0, 0.0]

        if "保修" in text or "质保" in text:
            return [0.0, 1.0]

        return [0.5, 0.5]


def create_store() -> PolicyVectorStore:
    """创建隔离的内存向量存储。"""

    return PolicyVectorStore(
        client=QdrantClient(":memory:"),
        collection_name="test-policies",
        embedder=FakePolicyEmbedding(),
    )


def create_documents() -> list[PolicyDocument]:
    """创建测试政策文档。"""

    return [
        PolicyDocument(
            policy_id="return-policy",
            title="退货政策",
            content="签收后 7 天内可以申请退货。",
        ),
        PolicyDocument(
            policy_id="warranty-policy",
            title="保修政策",
            content="手机和电脑提供 1 年有限保修。",
        ),
    ]


def test_upsert_and_search_policies() -> None:
    """政策应该能写入并按语义搜索。"""

    store = create_store()

    count = store.upsert_documents(create_documents())
    results = store.search("商品可以退货几天？")

    assert count == 2
    assert results
    assert results[0].policy_id == "return-policy"
    assert results[0].payload["title"] == "退货政策"


def test_search_returns_empty_for_missing_collection_or_query() -> None:
    """集合不存在或问题为空时应该返回空列表。"""

    store = create_store()

    assert store.search("退货政策") == []
    assert store.search("   ") == []


def test_search_rejects_non_positive_limit() -> None:
    """搜索数量必须大于零。"""

    store = create_store()

    with pytest.raises(ValueError, match="greater than zero"):
        store.search("退货政策", limit=0)