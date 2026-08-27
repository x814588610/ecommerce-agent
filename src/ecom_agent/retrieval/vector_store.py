"""商品的 Qdrant 向量存储。"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from ecom_agent.retrieval.documents import ProductDocument
from ecom_agent.retrieval.embeddings import EmbeddingProvider


@dataclass(frozen=True, slots=True)
class ProductSearchResult:
    """语义搜索返回的一个商品。"""

    product_id: str
    score: float
    payload: dict[str, object]


class ProductVectorStore:
    """在 Qdrant 中保存和搜索商品向量。"""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: EmbeddingProvider,
    ) -> None:
        """保存 Qdrant 客户端、集合名称和 Embedding 提供者。"""

        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder

    def ensure_collection(self) -> None:
        """当集合不存在时创建集合。"""

        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.embedder.dimension,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_documents(
        self,
        documents: Sequence[ProductDocument],
    ) -> int:
        """将商品文档转换为向量并保存到 Qdrant。"""

        document_list = list(documents)

        if not document_list:
            return 0

        self.ensure_collection()

        vectors = self.embedder.embed_documents(
            [document.text for document in document_list]
        )

        if len(vectors) != len(document_list):
            raise ValueError(
                "The number of vectors must match the number of documents."
            )

        points = [
            models.PointStruct(
                id=str(
                    uuid5(
                        NAMESPACE_URL,
                        f"ecommerce-agent:{document.product_id}",
                    )
                ),
                vector=vector,
                payload=document.payload,
            )
            for document, vector in zip(
                document_list,
                vectors,
                strict=True,
            )
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return len(points)

    def search(
        self,
        query: str,
        limit: int = 5,
        only_in_stock: bool = True,
        category: str | None = None,
        brand: str | None = None,
        max_price: Decimal | None = None,
    ) -> list[ProductSearchResult]:
        """根据语义相似度搜索商品。"""

        if not query.strip():
            return []

        if limit <= 0:
            raise ValueError("Search limit must be greater than zero.")

        if not self.client.collection_exists(self.collection_name):
            return []

        query_vector = self.embedder.embed_query(query)



        if max_price is not None and max_price < 0:
            raise ValueError("Maximum price must not be negative.")

        conditions = []

        if only_in_stock:
            conditions.append(
                models.FieldCondition(
                    key="stock",
                    range=models.Range(gt=0),
                )
            )

        if category:
            conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category),
                )
            )

        if brand:
            conditions.append(
                models.FieldCondition(
                    key="brand",
                    match=models.MatchValue(value=brand),
                )
            )

        if max_price is not None:
            conditions.append(
                models.FieldCondition(
                    key="price_value",
                    range=models.Range(lte=float(max_price)),
                )
            )

        query_filter = models.Filter(must=conditions) if conditions else None

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        results: list[ProductSearchResult] = []

        for point in response.points:
            payload = point.payload or {}
            product_id = payload.get("product_id")

            if not isinstance(product_id, str):
                continue

            results.append(
                ProductSearchResult(
                    product_id=product_id,
                    score=point.score,
                    payload=payload,
                )
            )

        return results
