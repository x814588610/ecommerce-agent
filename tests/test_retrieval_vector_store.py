"""Tests for the Qdrant product vector store."""

from collections.abc import Sequence

import pytest
from qdrant_client import QdrantClient

from ecom_agent.retrieval.documents import ProductDocument
from ecom_agent.retrieval.vector_store import ProductVectorStore


class FakeEmbedding:
    """A small deterministic embedding provider for tests."""

    dimension = 2

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Convert documents into deterministic two-dimensional vectors."""

        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Convert one query into a deterministic vector."""

        return self._embed(text)

    @staticmethod
    def _embed(text: str) -> list[float]:
        """Map phone and computer keywords to different vector directions."""

        if "手机" in text or "学习" in text:
            return [1.0, 0.0]

        if "电脑" in text or "编程" in text:
            return [0.0, 1.0]

        return [0.5, 0.5]


def create_document(
    product_id: str,
    text: str,
    stock: int,
) -> ProductDocument:
    """Create one retrieval document for testing."""

    return ProductDocument(
        product_id=product_id,
        text=text,
        payload={
            "product_id": product_id,
            "name": product_id,
            "stock": stock,
        },
    )


def create_store() -> ProductVectorStore:
    """Create an isolated in-memory vector store."""

    return ProductVectorStore(
        client=QdrantClient(":memory:"),
        collection_name="test-products",
        embedder=FakeEmbedding(),
    )


def test_upsert_and_search_products() -> None:
    """Documents should be stored and returned by semantic similarity."""

    store = create_store()

    count = store.upsert_documents(
        [
            create_document(
                "phone-001",
                "适合学生学习的手机",
                stock=20,
            ),
            create_document(
                "laptop-001",
                "适合编程的电脑",
                stock=15,
            ),
        ]
    )

    results = store.search("学习手机")

    assert count == 2
    assert results
    assert results[0].product_id == "phone-001"
    assert results[0].payload["stock"] == 20


def test_search_excludes_out_of_stock_products() -> None:
    """Out-of-stock products should be excluded by default."""

    store = create_store()

    store.upsert_documents(
        [
            create_document(
                "phone-001",
                "学习手机",
                stock=20,
            ),
            create_document(
                "phone-002",
                "备用手机",
                stock=0,
            ),
        ]
    )

    in_stock_results = store.search("手机")
    all_results = store.search(
        "手机",
        only_in_stock=False,
    )

    assert [result.product_id for result in in_stock_results] == [
        "phone-001"
    ]
    assert {
        result.product_id for result in all_results
    } == {"phone-001", "phone-002"}


def test_search_returns_empty_for_missing_collection_or_query() -> None:
    """Missing collections and blank queries should return no results."""

    store = create_store()

    assert store.search("手机") == []
    assert store.search("   ") == []


def test_search_rejects_non_positive_limit() -> None:
    """Search limit must be greater than zero."""

    store = create_store()

    with pytest.raises(ValueError, match="greater than zero"):
        store.search("手机", limit=0)