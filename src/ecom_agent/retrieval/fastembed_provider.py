"""使用 FastEmbed 在本地生成文本向量。"""

from collections.abc import Sequence

from fastembed import TextEmbedding

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"


class FastEmbedProvider:
    """使用 FastEmbed 生成多语言文本向量。"""

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        """加载指定的本地 Embedding 模型。"""

        self.model = TextEmbedding(model_name=model_name)
        self._dimension: int | None = None

    @property
    def dimension(self) -> int:
        """返回已加载模型的向量维度。"""

        if self._dimension is None:
            self._dimension = len(
                self.embed_query("dimension probe")
            )

        return self._dimension

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """将商品文档转换为文档向量。"""

        if not texts:
            return []

        vectors = self.model.embed(list(texts))

        return [self._to_list(vector) for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        """将用户问题转换为查询向量。"""

        vectors = self.model.embed([text])
        return self._to_list(next(iter(vectors)))

    @staticmethod
    def _to_list(values: object) -> list[float]:
        """将模型输出转换为普通 Python 列表。"""
        vector_values = (
            values.tolist()
            if hasattr(values, "tolist")
            else list(values)  # type: ignore[arg-type]
        )

        return [float(value) for value in vector_values]  # type: ignore[union-attr]
