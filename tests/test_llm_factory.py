"""Tests for the language model factory."""

import pytest
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from ecom_agent.llm.factory import create_chat_model
from ecom_agent.settings import Settings


def test_create_chat_model_from_settings() -> None:
    """The factory should create a configured ChatOpenAI instance."""

    settings = Settings(
        llm_base_url="https://example.test/v1",
        llm_model="test-model",
        llm_api_key=SecretStr("test-key"),
    )

    model = create_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "test-model"
    assert model.openai_api_base == "https://example.test/v1"
    assert model.temperature == 0


def test_create_chat_model_requires_api_key() -> None:
    """The factory should reject an empty API key."""

    settings = Settings(
        llm_api_key=SecretStr(""),
    )

    with pytest.raises(ValueError, match="LLM_API_KEY is not configured"):
        create_chat_model(settings)