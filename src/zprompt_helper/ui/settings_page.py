from typing import Protocol

from zprompt_helper.openrouter.client import OpenRouterClient


class OpenRouterConnectionClient(Protocol):
    def create_chat_completion(self, payload: dict) -> dict:
        ...


def build_settings_sections() -> list[dict[str, str]]:
    return [
        {"id": "api", "label": "API Access"},
        {"id": "model", "label": "Model Defaults"},
        {"id": "advanced", "label": "Advanced Generation"},
    ]


def normalize_settings_form(
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    api_key: str,
    theme_mode: str = "light",
) -> dict:
    return {
        "model": model.strip(),
        "temperature": float(temperature),
        "top_p": float(top_p),
        "max_tokens": int(max_tokens),
        "api_key": api_key.strip(),
        "theme_mode": "dark" if theme_mode == "dark" else "light",
    }


def save_settings_from_form(settings_service, form: dict) -> dict:
    normalized = normalize_settings_form(
        model=form.get("model", ""),
        temperature=form.get("temperature", 0.2),
        top_p=form.get("top_p", 0.9),
        max_tokens=form.get("max_tokens", 700),
        api_key=form.get("api_key", ""),
        theme_mode=form.get("theme_mode", "light"),
    )
    settings_service.save(**normalized)
    return normalized


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


def validate_settings_connection(
    api_key: str,
    model: str,
    client_factory=OpenRouterClient,
) -> bool:
    normalized_key = api_key.strip()
    if not normalized_key:
        raise ValueError("OpenRouter API key is required")
    return validate_connection(client_factory(normalized_key), model)


def render_settings_page(
    settings: dict,
    settings_service=None,
    client_factory=OpenRouterClient,
) -> None:
    import streamlit as st

    st.header("Настройки")
    for section in build_settings_sections():
        with st.container(border=True):
            st.subheader(section["label"])
            if section["id"] == "api":
                st.caption("Store the API key in the OS keyring, not in project files.")
            elif section["id"] == "model":
                st.caption("Use model defaults for generation requests across the workbench.")
            else:
                st.caption("Tune generation behavior without editing templates.")

    with st.form("settings-form"):
        api_key = st.text_input(
            "OpenRouter API Key",
            value=settings.get("api_key", ""),
            type="password",
            key="api_key",
        )
        model = st.text_input("Модель", value=settings.get("model", ""), key="model")
        temperature = st.number_input(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=float(settings.get("temperature", 0.2)),
            key="temperature",
        )
        top_p = st.number_input(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=float(settings.get("top_p", 0.9)),
            key="top_p",
        )
        max_tokens = st.number_input(
            "Max tokens",
            min_value=1,
            max_value=4096,
            value=int(settings.get("max_tokens", 700)),
            key="max_tokens",
        )
        submitted = st.form_submit_button("Сохранить", key="settings-form")

    form = {
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "api_key": api_key,
        "theme_mode": str(st.session_state.get("theme_mode", settings.get("theme_mode", "light"))),
    }
    if submitted:
        if settings_service is None:
            st.error("SettingsService is not configured.")
        else:
            try:
                save_settings_from_form(settings_service, form)
                st.success("Настройки сохранены.")
            except Exception as error:
                st.error(f"Не удалось сохранить настройки: {error}")
    if st.button("Проверить ключ", key="validate_api_key"):
        try:
            with _spinner(st, "Validating OpenRouter key..."):
                is_valid = validate_settings_connection(api_key, model, client_factory)
            if is_valid:
                _notify_success(st, "OpenRouter connection works.")
            else:
                st.error("OpenRouter did not return a valid response.")
        except Exception as error:
            st.error(f"Не удалось проверить ключ: {error}")


def _spinner(st_module, message: str):
    spinner = getattr(st_module, "spinner", None)
    if callable(spinner):
        return spinner(message)
    from contextlib import nullcontext

    return nullcontext()


def _notify_success(st_module, message: str) -> None:
    toast = getattr(st_module, "toast", None)
    if callable(toast):
        toast(message, icon=":material/check_circle:")
        return
    st_module.success(message)
