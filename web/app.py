"""Streamlit demo for the e-commerce agent."""

from uuid import uuid4

import httpx
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 30.0


def initialize_state() -> None:
    """Initialize values stored across Streamlit reruns."""

    if "session_id" not in st.session_state:
        st.session_state.session_id = f"demo-{uuid4().hex[:8]}"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_approval_id" not in st.session_state:
        st.session_state.pending_approval_id = None


def request_json(
    method: str,
    url: str,
    json_data: dict[str, object] | None = None,
) -> dict[str, object]:
    """Send an API request and return a JSON object."""

    try:
        response = httpx.request(
            method=method,
            url=url,
            json=json_data,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text

        raise RuntimeError(
            f"API 返回 {exc.response.status_code}：{detail}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(
            "无法连接 FastAPI 服务，请确认服务已经启动。"
        ) from exc

    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError("API 返回了无效的数据格式。")

    return data


def add_message(role: str, content: str) -> None:
    """Append one message to the visible chat history."""

    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
        }
    )


def start_new_session() -> None:
    """Clear the page and generate a new conversation ID."""

    st.session_state.session_id = f"demo-{uuid4().hex[:8]}"
    st.session_state.messages = []
    st.session_state.pending_approval_id = None


def decide_approval(
    api_base_url: str,
    approval_id: str,
    approved: bool,
) -> None:
    """Submit a human decision for one approval request."""

    data = request_json(
        method="POST",
        url=f"{api_base_url}/approvals/{approval_id}/decision",
        json_data={"approved": approved},
    )

    status = data.get("status")
    status_text = "已批准" if status == "approved" else "已拒绝"

    add_message(
        role="assistant",
        content=f"审批请求 `{approval_id}` {status_text}。",
    )
    st.session_state.pending_approval_id = None


st.set_page_config(
    page_title="电商智能客服",
    page_icon=":material/shopping_bag:",
    layout="wide",
)

initialize_state()

with st.sidebar:
    st.header("会话设置")

    api_base_url = st.text_input(
        "FastAPI 地址",
        value=DEFAULT_API_URL,
    ).rstrip("/")

    user_id = st.text_input(
        "用户 ID",
        value="demo-user",
    )

    st.text_input(
        "会话 ID",
        value=st.session_state.session_id,
        disabled=True,
    )

    if st.button(
        "检测 API",
        icon=":material/monitor_heart:",
        width="stretch",
    ):
        try:
            health = request_json(
                method="GET",
                url=f"{api_base_url}/health",
            )
            st.success(f"API 状态：{health.get('status', 'unknown')}")
        except RuntimeError as exc:
            st.error(str(exc))

    if st.button(
        "新建会话",
        icon=":material/add_comment:",
        width="stretch",
    ):
        start_new_session()
        st.rerun()

    pending_approval_id = st.session_state.pending_approval_id

    if pending_approval_id:
        st.subheader("待处理审批")
        st.code(pending_approval_id)

        approve_column, reject_column = st.columns(2)

        if approve_column.button(
            "批准",
            icon=":material/check:",
            type="primary",
            width="stretch",
        ):
            try:
                decide_approval(
                    api_base_url=api_base_url,
                    approval_id=pending_approval_id,
                    approved=True,
                )
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))

        if reject_column.button(
            "拒绝",
            icon=":material/close:",
            width="stretch",
        ):
            try:
                decide_approval(
                    api_base_url=api_base_url,
                    approval_id=pending_approval_id,
                    approved=False,
                )
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))

st.title("电商智能客服")
st.caption(f"当前会话：{st.session_state.session_id}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input(
    "输入商品咨询、库存查询或售后请求",
    max_chars=2000,
)

if user_message:
    add_message("user", user_message)

    with st.chat_message("user"):
        st.markdown(user_message)

    try:
        with st.spinner("正在处理请求..."):
            result = request_json(
                method="POST",
                url=f"{api_base_url}/chat",
                json_data={
                    "message": user_message,
                    "session_id": st.session_state.session_id,
                    "user_id": user_id,
                },
            )

        answer = result.get("answer")

        if not isinstance(answer, str) or not answer:
            raise RuntimeError("Agent 没有返回有效回答。")

        add_message("assistant", answer)

        approval_id = result.get("approval_id")
        if isinstance(approval_id, str) and approval_id:
            st.session_state.pending_approval_id = approval_id

        st.rerun()
    except RuntimeError as exc:
        with st.chat_message("assistant"):
            st.error(str(exc))