from typing import Protocol


class OpenRouterConnectionClient(Protocol):
    def create_chat_completion(self, payload: dict) -> dict:
        ...


def normalize_settings_form(
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    api_key: str,
) -> dict:
    return {
        "model": model.strip(),
        "temperature": float(temperature),
        "top_p": float(top_p),
        "max_tokens": int(max_tokens),
        "api_key": api_key.strip(),
    }


def validate_connection(client: OpenRouterConnectionClient, model: str) -> bool:
    payload = {
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    normalized_model = model.strip()
    if normalized_model:
        payload["model"] = normalized_model

    response = client.create_chat_completion(payload)
    return bool(response.get("choices"))


def render_settings_page(settings: dict) -> None:
    import streamlit as st

    st.header("Настройки")
    st.text_input(
        "OpenRouter API Key",
        value=settings.get("api_key", ""),
        type="password",
        key="api_key",
    )
    st.text_input("Модель", value=settings.get("model", ""), key="model")
    st.number_input(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=float(settings.get("temperature", 0.2)),
        key="temperature",
    )
    st.number_input(
        "Top P",
        min_value=0.0,
        max_value=1.0,
        value=float(settings.get("top_p", 0.9)),
        key="top_p",
    )
    st.number_input(
        "Max tokens",
        min_value=1,
        max_value=4096,
        value=int(settings.get("max_tokens", 700)),
        key="max_tokens",
    )
    st.button("Сохранить", key="save_settings")
    st.button("Проверить ключ", key="validate_api_key")
