"""Factory functions for language models."""

from langchain_openai import ChatOpenAI

from ecom_agent.settings import Settings, get_settings


def create_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    """Create a chat model using the application settings."""

    app_settings = settings if settings is not None else get_settings()
    api_key = app_settings.llm_api_key.get_secret_value().strip()

    if not api_key:
        raise ValueError("LLM_API_KEY is not configured.")

    return ChatOpenAI(
        model=app_settings.llm_model,
        base_url=app_settings.llm_base_url,
        api_key=api_key,
        temperature=0,
    )