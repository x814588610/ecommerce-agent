"""测试售后政策搜索工具。"""

import json

from langchain_core.tools import StructuredTool

from ecom_agent.agent.tools import create_policy_search_tool
from ecom_agent.retrieval.policy_vector_store import PolicySearchResult


class FakePolicyVectorStore:
    """用于测试的固定政策向量存储。"""

    def __init__(self, results: list[PolicySearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[PolicySearchResult]:
        """记录搜索参数并返回固定结果。"""

        self.calls.append((query, limit))
        return self.results[:limit]


def create_policy_result() -> PolicySearchResult:
    """创建一条测试政策结果。"""

    return PolicySearchResult(
        policy_id="return-policy",
        score=0.91,
        payload={
            "title": "退货政策",
            "content": "商品签收后 7 天内可以申请退货。",
            "source": "本地售后政策",
        },
    )


def test_create_policy_search_tool() -> None:
    """工厂应该返回配置好的政策搜索工具。"""

    vector_store = FakePolicyVectorStore(
        results=[create_policy_result()]
    )

    search_tool = create_policy_search_tool(vector_store)

    assert isinstance(search_tool, StructuredTool)
    assert search_tool.name == "search_policy"
    assert "query" in search_tool.args
    assert "limit" in search_tool.args


def test_policy_search_tool_returns_source_and_content() -> None:
    """工具结果应该包含政策内容和来源。"""

    vector_store = FakePolicyVectorStore(
        results=[create_policy_result()]
    )
    search_tool = create_policy_search_tool(vector_store)

    raw_result = search_tool.invoke(
        {
            "query": "签收后几天可以退货？",
            "limit": 3,
        }
    )

    result = json.loads(raw_result)

    assert result["total"] == 1
    assert result["items"][0] == {
        "policy_id": "return-policy",
        "title": "退货政策",
        "content": "商品签收后 7 天内可以申请退货。",
        "score": 0.91,
        "source": "本地售后政策",
    }
    assert vector_store.calls == [
        ("签收后几天可以退货？", 3)
    ]


def test_policy_search_tool_returns_empty_result() -> None:
    """没有匹配政策时应该返回空结果。"""

    vector_store = FakePolicyVectorStore(results=[])
    search_tool = create_policy_search_tool(vector_store)

    raw_result = search_tool.invoke({"query": "未知政策"})

    assert json.loads(raw_result) == {
        "items": [],
        "total": 0,
    }