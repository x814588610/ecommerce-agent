"""检索使用的 Embedding 提供者接口。"""


from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """将文本转换为向量以进行语义搜索。"""

    dimension: int

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """将多个文档转换为向量。"""
        ...

    def embed_query(self, text: str) -> list[float]:
        """将一个搜索问题转换为向量。"""
        ...
