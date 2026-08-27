"""建立售后政策检索索引。"""

from ecom_agent.retrieval.factory import (
    get_embedding_provider,
    get_policy_vector_store,
    get_qdrant_client,
)
from ecom_agent.retrieval.policy_indexer import index_policies


def rebuild_policy_index() -> int:
    """读取默认售后政策并写入 Qdrant。"""

    vector_store = get_policy_vector_store()

    try:
        return index_policies(vector_store)
    finally:
        vector_store.client.close()
        get_policy_vector_store.cache_clear()
        get_qdrant_client.cache_clear()
        get_embedding_provider.cache_clear()


if __name__ == "__main__":
    indexed_count = rebuild_policy_index()
    print(f"已索引售后政策数量：{indexed_count}")