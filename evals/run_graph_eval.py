"""运行电商 Agent 的 LangGraph 规则评估。"""

import json
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool, tool

from ecom_agent.agent.graph import build_commerce_graph
from ecom_agent.agent.state import create_initial_state

CASE_FILE = Path(__file__).with_name("agent_cases.json")


@tool
def search_products(query: str) -> str:
    """模拟关键词商品搜索。"""

    return "关键词商品搜索结果"


@tool
def semantic_search_products(query: str) -> str:
    """模拟商品语义搜索。"""

    return "商品语义搜索结果"


@tool
def get_product_detail(product_id: str) -> str:
    """模拟商品详情查询。"""

    return f"商品详情：{product_id}"


@tool
def check_inventory(product_id: str) -> str:
    """模拟商品库存查询。"""

    return f"商品库存：{product_id}"


@tool
def search_policy(query: str) -> str:
    """模拟售后政策搜索。"""

    return "售后政策搜索结果"


AVAILABLE_TOOLS: list[BaseTool] = [
    search_products,
    semantic_search_products,
    get_product_detail,
    check_inventory,
    search_policy,
]


class FakeModel:
    """按照评估案例返回固定工具调用的测试模型。"""

    def __init__(
        self,
        tool_name: str,
    ) -> None:
        """保存本次评估要调用的工具名称。"""

        self.tool_name = tool_name
        self.calls: list[list[object]] = []

    def bind_tools(
        self,
        tools: list[BaseTool],
    ) -> "FakeModel":
        """接收图绑定的工具。"""

        return self

    def invoke(
        self,
        messages: list[object],
    ) -> AIMessage:
        """第一次请求工具，第二次返回最终回答。"""

        self.calls.append(messages)

        if len(self.calls) == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": self.tool_name,
                        "args": self._tool_args(),
                        "id": "eval-tool-call",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(content="评估用最终回答。")

    def _tool_args(self) -> dict[str, str]:
        """根据工具名称生成测试参数。"""

        if self.tool_name in {
            "search_products",
            "semantic_search_products",
            "search_policy",
        }:
            return {"query": "评估问题"}

        return {"product_id": "phone-001"}


def load_cases() -> list[dict[str, object]]:
    """读取固定评估案例。"""

    data = json.loads(
        CASE_FILE.read_text(encoding="utf-8")
    )
    cases = data.get("cases")

    if not isinstance(cases, list):
        raise ValueError("评估文件必须包含 cases 列表。")

    return cases


def evaluate_case(case: dict[str, object]) -> list[str]:
    """运行一个案例的 LangGraph 评估。"""

    case_id = case.get("case_id", "unknown")
    message = case.get("message", "")
    expected_intent = case.get("expected_intent")
    expected_tool = case.get("expected_tool")

    if not isinstance(message, str):
        return [f"{case_id}: message 必须是字符串"]

    if not isinstance(expected_tool, str):
        return []

    model = FakeModel(expected_tool)
    graph = build_commerce_graph(
        model,
        AVAILABLE_TOOLS,
    )
    result = graph.invoke(
        create_initial_state(message)
    )

    failures: list[str] = []

    if result.get("intent") != expected_intent:
        failures.append(
            f"意图错误，实际为 {result.get('intent')}，"
            f"预期为 {expected_intent}"
        )

    if result.get("answer") != "评估用最终回答。":
        failures.append(
            f"没有得到预期最终回答：{result.get('answer')}"
        )

    if result.get("step_count") != 2:
        failures.append(
            f"执行步数错误，实际为 {result.get('step_count')}，"
            "预期为 2"
        )

    if len(model.calls) != 2:
        failures.append(
            f"模型调用次数错误，实际为 {len(model.calls)}，"
            "预期为 2"
        )

    messages = result.get("messages", [])

    if not messages or messages[-2].type != "tool":
        failures.append("工具消息没有出现在最终回答之前")

    return failures


def main() -> None:
    """运行全部 Graph 评估案例。"""

    cases = load_cases()
    passed_count = 0
    skipped_count = 0
    failed_count = 0

    for case in cases:
        case_id = case.get("case_id", "unknown")
        expected_tool = case.get("expected_tool")

        if not isinstance(expected_tool, str):
            skipped_count += 1
            print(f"SKIP: {case_id}")
            continue

        failures = evaluate_case(case)

        if failures:
            failed_count += 1
            print(f"FAIL: {case_id}")

            for failure in failures:
                print(f"  - {failure}")
        else:
            passed_count += 1
            print(f"PASS: {case_id}")

    print(
        f"RESULT: {passed_count} passed, "
        f"{skipped_count} skipped, "
        f"{failed_count} failed"
    )

    if failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()