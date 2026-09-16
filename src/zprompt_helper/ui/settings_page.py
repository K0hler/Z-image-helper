from typing import Protocol

from zprompt_helper.openrouter.client import (
    DEFAULT_BASE_URL,
    OpenRouterClient,
    normalize_base_url,
)


class ModelCatalogClient(Protocol):
    def list_models(self) -> list[str]:
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
    base_url: str = DEFAULT_BASE_URL,
    theme_mode: str = "light",
) -> dict:
    return {
        "model": model.strip(),
        "base_url": normalize_base_url(base_url),
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
        base_url=form.get("base_url", DEFAULT_BASE_URL),
        theme_mode=form.get("theme_mode", "light"),
    )
    settings_service.save(**normalized)
    return normalized


def fetch_available_models(
    api_key: str,
    base_url: str,
    client_factory=OpenRouterClient,
) -> list[str]:
    normalized_key = api_key.strip()
    if not normalized_key:
        raise ValueError("API key is required")
    normalized_url = normalize_base_url(base_url)
    models = client_factory(normalized_key, normalized_url).list_models()
    if not models:
        raise ValueError("API returned no available models")
    return models


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
                st.caption(
                    "Use an OpenAI-compatible API base URL. The API key stays in the OS keyring."
                )
            elif section["id"] == "model":
                st.caption("Load available models from the service, then choose the default.")
            else:
                st.caption("Tune generation behavior without editing templates.")

    with st.form("settings-form"):
        api_key = st.text_input(
            "API Key",
            value=settings.get("api_key", ""),
            type="password",
            key="api_key",
        )
        base_url = st.text_input(
            "Base URL",
            value=settings.get("base_url", DEFAULT_BASE_URL),
            key="base_url",
            help="Корневой URL OpenAI-совместимого API, например http://localhost:1234/v1",
        )
        normalized_url = base_url.strip().rstrip("/")
        available_models = st.session_state.get("available_models", [])
        catalog_matches = (
            isinstance(available_models, list)
            and bool(available_models)
            and st.session_state.get("available_models_base_url") == normalized_url
        )
        if catalog_matches:
            current_model = str(
                st.session_state.get("model", settings.get("model", ""))
            ).strip()
            selected_model = str(st.session_state.get("model_from_catalog", ""))
            if selected_model not in available_models:
                st.session_state["model_from_catalog"] = (
                    current_model if current_model in available_models else available_models[0]
                )
            model = st.selectbox(
                "Модель",
                options=available_models,
                key="model_from_catalog",
            )
        else:
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
        fetch_models = st.form_submit_button(
            "Проверить и загрузить модели",
            key="fetch_models",
        )

    form = {
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "api_key": api_key,
        "theme_mode": str(st.session_state.get("theme_mode", settings.get("theme_mode", "light"))),
    }
    if fetch_models:
        try:
            with _spinner(st, "Проверяю сервис и загружаю модели..."):
                models = fetch_available_models(api_key, base_url, client_factory)
            normalized_url = normalize_base_url(base_url)
            current_model = str(model).strip()
            st.session_state["available_models"] = models
            st.session_state["available_models_base_url"] = normalized_url
            st.session_state["model_from_catalog"] = (
                current_model if current_model in models else models[0]
            )
            _notify_success(st, f"Сервис доступен. Загружено моделей: {len(models)}.")
            st.rerun()
        except Exception as error:
            st.error(f"Не удалось загрузить модели: {error}")
        return

    if submitted:
        if settings_service is None:
            st.error("SettingsService is not configured.")
        else:
            try:
                save_settings_from_form(settings_service, form)
                st.success("Настройки сохранены.")
            except Exception as error:
                st.error(f"Не удалось сохранить настройки: {error}")


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
