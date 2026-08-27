"""将售后政策同步到向量数据库。"""

from collections.abc import Sequence

from ecom_agent.retrieval.policy_documents import (
    PolicyDocument,
    get_default_policy_documents,
)
from ecom_agent.retrieval.policy_vector_store import PolicyVectorStore


def index_policies(
    vector_store: PolicyVectorStore,
    documents: Sequence[PolicyDocument] | None = None,
) -> int:
    """将售后政策文档写入政策向量库。"""

    policy_documents = (
        list(documents)
        if documents is not None
        else get_default_policy_documents()
    )

    return vector_store.upsert_documents(policy_documents)