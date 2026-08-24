"""Tests for commerce agent prompts."""

from ecom_agent.llm.prompts import (
    CUSTOMER_SERVICE_SYSTEM_PROMPT,
    create_customer_service_prompt,
)


def test_system_prompt_contains_business_rules() -> None:
    """The system prompt should contain the core commerce rules."""

    assert "必须优先调用工具" in CUSTOMER_SERVICE_SYSTEM_PROMPT
    assert "不得编造价格" in CUSTOMER_SERVICE_SYSTEM_PROMPT
    assert "缺货商品不能作为正常推荐结果" in CUSTOMER_SERVICE_SYSTEM_PROMPT
    assert "必须请求人工审批" in CUSTOMER_SERVICE_SYSTEM_PROMPT


def test_prompt_formats_user_messages() -> None:
    """The prompt should combine system and user messages."""

    prompt = create_customer_service_prompt()

    result = prompt.invoke(
        {
            "messages": [
                ("user", "我想找 3000 元以内的手机"),
            ]
        }
    )

    assert len(result.messages) == 2
    assert result.messages[0].type == "system"
    assert result.messages[1].type == "human"
    assert result.messages[1].content == "我想找 3000 元以内的手机"