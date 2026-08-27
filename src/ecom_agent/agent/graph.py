"""电商 Agent 的 LangGraph 工作流。"""

import json
from collections.abc import Sequence
from time import perf_counter

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ecom_agent.agent.intents import (
    classify_intent,
    is_tool_allowed,
)
from ecom_agent.agent.state import AgentState
from ecom_agent.agent.telemetry import (
    log_agent_error,
    log_model_call,
    log_tool_call,
)
from ecom_agent.llm.prompts import CUSTOMER_SERVICE_SYSTEM_PROMPT

MAX_AGENT_STEPS = 6
NO_RESULTS_ANSWER = (
    "没有找到符合条件的商品，你可以调整关键词、品牌或价格范围后重试。"
)

def _has_tool_calls(message: object) -> bool:
    """检查模型是否请求调用工具。"""

    return bool(getattr(message, "tool_calls", []))


def _content_to_text(content: object) -> str:
    """将模型内容转换为最终回答文本。"""

    if isinstance(content, str):
        return content

    return str(content)

def _tool_result_is_empty(
    tool_name: str,
    result: object,
) -> bool:
    """判断商品搜索工具是否没有返回结果。"""

    if not isinstance(result, str):
        return False

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return False

    if tool_name == "search_products":
        return isinstance(data, list) and not data

    if tool_name == "semantic_search_products":
        if not isinstance(data, dict):
            return False

        items = data.get("items")
        return isinstance(items, list) and not items

    return False


def _is_user_message(message: object) -> bool:
    """判断一条消息是否来自用户。"""

    if isinstance(message, dict):
        return message.get("role") in {"user", "human"}

    return getattr(message, "type", "") in {"user", "human"}


def _message_to_text(message: object) -> str:
    """提取消息中的文本内容。"""

    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")

    return content if isinstance(content, str) else str(content)

def _latest_user_message(messages: Sequence[object]) -> str:
    """从消息历史中获取最近一条用户消息。"""

    for message in reversed(messages):
        if _is_user_message(message):
            return _message_to_text(message)

    return ""

def classify_intent_node(state: AgentState) -> dict[str, object]:
    """识别用户意图并写入 Agent 状态。"""

    messages = state.get("messages", [])
    user_message = _latest_user_message(messages)

    return {
        "intent": classify_intent(user_message),
    }


def _tool_calls_are_allowed(
    message: object,
    state: AgentState,
    available_tool_names: Sequence[str],
) -> bool:
    """检查模型请求的全部工具是否符合当前意图。"""

    tool_calls = getattr(message, "tool_calls", [])

    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            return False

        tool_name = tool_call.get("name")

        if not isinstance(tool_name, str):
            return False

        if not is_tool_allowed(
            intent=state.get("intent", "general"),
            tool_name=tool_name,
            available_tool_names=available_tool_names,
        ):
            return False

    return True


def build_commerce_graph(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
) -> CompiledStateGraph:
    """构建并编译电商 Agent 图。"""

    tool_list = list(tools)

    if not tool_list:
        raise ValueError("At least one commerce tool is required.")

    model_with_tools = model.bind_tools(tool_list)
    tools_by_name = {tool.name: tool for tool in tool_list}

    def agent_node(state: AgentState) -> dict[str, object]:
        """调用一次模型。"""
        intent = state.get("intent", "general")
        system_content = (
            f"{CUSTOMER_SERVICE_SYSTEM_PROMPT}\n\n"
            f"当前请求意图：{intent}"
        )
        messages = [
            SystemMessage(content=system_content),
            *state.get("messages", []),
        ]
        started_at = perf_counter()
        try:
            response = model_with_tools.invoke(messages)
        except Exception as exc:
            log_agent_error(exc)
            raise
        finally:
            log_model_call(
                tool_names=[tool.name for tool in tool_list],
                elapsed_ms=(perf_counter() - started_at) * 1000,
            ) 
        step_count = state.get("step_count", 0) + 1

        updates: dict[str, object] = {
            "messages": [response],
            "step_count": step_count,
        }

        if not _has_tool_calls(response):
            updates["answer"] = _content_to_text(response.content)

        return updates
    
    def disallowed_tool_node(state: AgentState) -> dict[str, object]:
        """阻止与当前意图不匹配的工具调用。"""

        response = AIMessage(
            content="当前请求与工具不匹配，我暂时无法执行该操作。"
        )

        return {
            "messages": [response],
            "answer": response.content,
        }

    def execute_tools_node(state: AgentState) -> dict[str, object]:
        """执行模型请求的工具，并把异常转换为安全状态。"""

        messages = state.get("messages", [])
        if not messages:
            return {"error": "工具执行时没有找到模型消息"}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        tool_messages: list[ToolMessage] = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            tool_args = tool_call.get("args", {})

            if not isinstance(tool_name, str):
                error = "工具名称无效"
            elif not isinstance(tool_call_id, str):
                error = "工具调用编号无效"
            elif not isinstance(tool_args, dict):
                error = "工具参数无效"
            else:
                started_at = perf_counter()

                try:
                    result = tools_by_name[tool_name].invoke(tool_args)
                except Exception as exc:
                    log_tool_call(
                        tool_name=tool_name,
                        elapsed_ms=(perf_counter() - started_at) * 1000,
                        success=False,
                    )
                    log_agent_error(exc)
                    error = str(exc)
                else:
                    log_tool_call(
                        tool_name=tool_name,
                        elapsed_ms=(perf_counter() - started_at) * 1000,
                        success=True,
                    )

                    result_text = (
                        result
                        if isinstance(result, str)
                        else str(result)
                    )
                    tool_messages.append(
                        ToolMessage(
                            content=result_text,
                            tool_call_id=tool_call_id,
                        )
                    )

                    if _tool_result_is_empty(tool_name, result_text):
                        return {
                            "messages": tool_messages,
                            "answer": NO_RESULTS_ANSWER,
                        }

                    continue

            error_message = ToolMessage(
                content=f"工具执行失败：{error}",
                tool_call_id=str(tool_call_id or "unknown-tool-call"),
            )
            tool_messages.append(error_message)

            return {
                "messages": tool_messages,
                "error": error,
                "answer": "商品查询暂时不可用，请稍后重试。",
            }

        return {"messages": tool_messages}

    def max_steps_node(state: AgentState) -> dict[str, object]:
        """达到步数上限时返回安全回答。"""

        response = AIMessage(
            content="我暂时无法完成这次查询，请稍后重试。"
        )

        return {
            "messages": [response],
            "answer": response.content,
        }

    def route_after_agent(state: AgentState) -> str:
        """选择调用工具、停止或安全退出。"""

        messages = state.get("messages", [])
        if not messages:
            return END

        last_message = messages[-1]

        if _has_tool_calls(last_message):
            available_tool_names = [
                tool.name
                for tool in tool_list
            ]

            if not _tool_calls_are_allowed(
                message=last_message,
                state=state,
                available_tool_names=available_tool_names,
            ):
                return "disallowed_tool"

            if state.get("step_count", 0) >= MAX_AGENT_STEPS:
                return "max_steps"

            return "tools"

        return END

    def route_after_tools(state: AgentState) -> str:
        """工具成功时继续请求模型，失败时直接结束。"""

        if state.get("error") or state.get("answer"):
                return END

        return "agent"

    workflow = StateGraph(AgentState)

    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", execute_tools_node)
    workflow.add_node("max_steps", max_steps_node)
    workflow.add_node("disallowed_tool", disallowed_tool_node)

    workflow.add_edge(START, "classify_intent")
    workflow.add_edge("classify_intent", "agent")

    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "max_steps": "max_steps",
            "disallowed_tool": "disallowed_tool",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "agent": "agent",
            END: END,
        },
    )
    workflow.add_edge("max_steps", END)
    workflow.add_edge("disallowed_tool", END)

    return workflow.compile()
