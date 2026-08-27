"""创建并缓存商品检索所需的组件。"""

from functools import lru_cache

from qdrant_client import QdrantClient

from ecom_agent.retrieval.fastembed_provider import FastEmbedProvider
from ecom_agent.retrieval.policy_vector_store import PolicyVectorStore
from ecom_agent.retrieval.vector_store import ProductVectorStore
from ecom_agent.settings import get_settings


@lru_cache
def get_embedding_provider() -> FastEmbedProvider:
    """创建并缓存本地文本向量模型。"""

    return FastEmbedProvider()


@lru_cache
def get_qdrant_client() -> QdrantClient:
    """根据配置创建并缓存 Qdrant 客户端。"""

    settings = get_settings()

    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)

    return QdrantClient(path=settings.qdrant_path)


@lru_cache
def get_product_vector_store() -> ProductVectorStore:
    """组装并缓存商品向量存储。"""

    settings = get_settings()

    return ProductVectorStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_collection,
        embedder=get_embedding_provider(),
    )

@lru_cache
def get_policy_vector_store() -> PolicyVectorStore:
    """组装并缓存售后政策向量存储。"""

    settings = get_settings()

    return PolicyVectorStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_policy_collection,
        embedder=get_embedding_provider(),
    )