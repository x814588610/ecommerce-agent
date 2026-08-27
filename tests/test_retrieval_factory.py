"""测试检索组件工厂。"""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest

import ecom_agent.retrieval.factory as factory


@pytest.fixture(autouse=True)
def clear_factory_caches() -> Iterator[None]:
    """在每个测试前后清除工厂缓存。"""

    factory.get_embedding_provider.cache_clear()
    factory.get_qdrant_client.cache_clear()
    factory.get_product_vector_store.cache_clear()
    factory.get_policy_vector_store.cache_clear()

    yield

    factory.get_embedding_provider.cache_clear()
    factory.get_qdrant_client.cache_clear()
    factory.get_product_vector_store.cache_clear()
    factory.get_policy_vector_store.cache_clear()


def test_embedding_provider_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """本地向量模型应该只创建一次。"""

    created_providers: list[object] = []

    class FakeEmbeddingProvider:
        """代替真实 FastEmbed 模型的测试对象。"""

        def __init__(self) -> None:
            created_providers.append(self)

    monkeypatch.setattr(
        factory,
        "FastEmbedProvider",
        FakeEmbeddingProvider,
    )

    first_provider = factory.get_embedding_provider()
    second_provider = factory.get_embedding_provider()

    assert first_provider is second_provider
    assert len(created_providers) == 1


def test_qdrant_client_uses_configured_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Qdrant 客户端应该使用配置中的服务地址。"""

    created_urls: list[str] = []

    class FakeQdrantClient:
        """记录连接地址的测试 Qdrant 客户端。"""

        def __init__(self, url: str) -> None:
            self.url = url
            created_urls.append(url)

    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: SimpleNamespace(qdrant_url="http://qdrant.test:6333"),
    )
    monkeypatch.setattr(
        factory,
        "QdrantClient",
        FakeQdrantClient,
    )

    first_client = factory.get_qdrant_client()
    second_client = factory.get_qdrant_client()

    assert first_client is second_client
    assert first_client.url == "http://qdrant.test:6333"
    assert created_urls == ["http://qdrant.test:6333"]


def test_product_vector_store_is_assembled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """商品向量存储应该包含客户端、集合名称和向量模型。"""

    fake_client = object()
    fake_embedder = object()

    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: SimpleNamespace(qdrant_collection="test-products"),
    )
    monkeypatch.setattr(
        factory,
        "get_qdrant_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        factory,
        "get_embedding_provider",
        lambda: fake_embedder,
    )

    first_store = factory.get_product_vector_store()
    second_store = factory.get_product_vector_store()

    assert first_store is second_store
    assert first_store.client is fake_client
    assert first_store.collection_name == "test-products"
    assert first_store.embedder is fake_embedder


def test_policy_vector_store_is_assembled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """售后政策向量存储应该使用独立集合。"""

    fake_client = object()
    fake_embedder = object()

    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: SimpleNamespace(
            qdrant_policy_collection="test-policies",
        ),
    )
    monkeypatch.setattr(
        factory,
        "get_qdrant_client",
        lambda: fake_client,
    )
    monkeypatch.setattr(
        factory,
        "get_embedding_provider",
        lambda: fake_embedder,
    )

    store = factory.get_policy_vector_store()

    assert store.client is fake_client
    assert store.collection_name == "test-policies"
    assert store.embedder is fake_embedder