"""售后政策的 Qdrant 向量存储。"""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from ecom_agent.retrieval.embeddings import EmbeddingProvider
from ecom_agent.retrieval.policy_documents import PolicyDocument


class PolicySearchResult:
    """售后政策语义搜索结果。"""

    def __init__(
        self,
        policy_id: str,
        score: float,
        payload: dict[str, object],
    ) -> None:
        """保存政策编号、相似度和政策元数据。"""

        self.policy_id = policy_id
        self.score = score
        self.payload = payload


class PolicyVectorStore:
    """在 Qdrant 中保存和搜索售后政策。"""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedder: EmbeddingProvider,
    ) -> None:
        """保存 Qdrant 客户端、集合名称和向量模型。"""

        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder

    def ensure_collection(self) -> None:
        """当政策集合不存在时创建集合。"""

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
        documents: Sequence[PolicyDocument],
    ) -> int:
        """将政策文档向量化并保存到 Qdrant。"""

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
                        f"ecommerce-agent:policy:{document.policy_id}",
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
    ) -> list[PolicySearchResult]:
        """根据用户问题搜索相关售后政策。"""

        if not query.strip():
            return []

        if limit <= 0:
            raise ValueError("Search limit must be greater than zero.")

        if not self.client.collection_exists(self.collection_name):
            return []

        query_vector = self.embedder.embed_query(query)

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )

        results: list[PolicySearchResult] = []

        for point in response.points:
            payload = point.payload or {}
            policy_id = payload.get("policy_id")

            if not isinstance(policy_id, str):
                continue

            results.append(
                PolicySearchResult(
                    policy_id=policy_id,
                    score=point.score,
                    payload=payload,
                )
            )

        return results