"""运行电商 Agent 的规则评估。"""

import json
from pathlib import Path

from ecom_agent.agent.intents import (
    classify_intent,
    is_tool_allowed,
)
from ecom_agent.agent.policies import assess_risk

CASE_FILE = Path(__file__).with_name("agent_cases.json")

AVAILABLE_TOOL_NAMES = (
    "search_products",
    "semantic_search_products",
    "get_product_detail",
    "check_inventory",
    "search_policy",
    "get_order_status",
)


def load_cases() -> list[dict[str, object]]:
    """读取固定评估案例。"""

    data = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases")

    if not isinstance(cases, list):
        raise ValueError("评估文件必须包含 cases 列表。")

    return cases


def evaluate_case(case: dict[str, object]) -> list[str]:
    """评估单个案例并返回错误列表。"""

    case_id = case.get("case_id", "unknown")
    message = case.get("message", "")
    expected_intent = case.get("expected_intent")
    expected_risk = case.get("expected_risk")
    expected_approval = case.get("expected_approval")
    expected_tool = case.get("expected_tool")

    if not isinstance(message, str):
        return [f"{case_id}: message 必须是字符串"]

    actual_intent = classify_intent(message)
    actual_risk, actual_approval = assess_risk(message)

    failures: list[str] = []

    if actual_intent != expected_intent:
        failures.append(f"意图错误，实际为 {actual_intent}，预期为 {expected_intent}")

    if actual_risk != expected_risk:
        failures.append(f"风险等级错误，实际为 {actual_risk}，预期为 {expected_risk}")

    if actual_approval != expected_approval:
        failures.append(f"审批判断错误，实际为 {actual_approval}，预期为 {expected_approval}")

    if isinstance(expected_tool, str):
        tool_allowed = is_tool_allowed(
            intent=actual_intent,
            tool_name=expected_tool,
            available_tool_names=AVAILABLE_TOOL_NAMES,
        )

        if not tool_allowed:
            failures.append(f"工具 {expected_tool} 不被意图 {actual_intent} 允许")

    return failures


def main() -> None:
    """运行全部规则评估案例。"""

    cases = load_cases()
    failed_count = 0

    for case in cases:
        case_id = case.get("case_id", "unknown")
        failures = evaluate_case(case)

        if failures:
            failed_count += 1
            print(f"FAIL: {case_id}")

            for failure in failures:
                print(f"  - {failure}")
        else:
            print(f"PASS: {case_id}")

    passed_count = len(cases) - failed_count
    print(f"RESULT: {passed_count} passed, {failed_count} failed")

    if failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
