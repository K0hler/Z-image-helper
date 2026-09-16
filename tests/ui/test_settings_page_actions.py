from zprompt_helper.ui.settings_page import (
    build_settings_sections,
    fetch_available_models,
    normalize_settings_form,
    render_settings_page,
    save_settings_from_form,
)


class FakeClient:
    def __init__(self, models: list[str] | None = None) -> None:
        self.models = models or ["alpha-model", "zeta-model"]
        self.list_models_calls = 0

    def list_models(self) -> list[str]:
        self.list_models_calls += 1
        return self.models


class FakeSettingsService:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(self, **kwargs) -> None:
        self.saved.append(kwargs)


class FakeContext:
    def __init__(self, streamlit: "FakeStreamlit", label: str | None = None) -> None:
        self.streamlit = streamlit
        self.label = label

    def __enter__(self):
        if self.label is not None:
            self.streamlit.entered_contexts.append(self.label)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class FakeContainer(FakeContext):
    pass


class FakeForm(FakeContext):
    pass


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.entered_contexts: list[str] = []
        self.forms: list[str] = []
        self.spinner_messages: list[str] = []
        self.container_borders: list[bool] = []
        self.successes: list[str] = []
        self.errors: list[str] = []
        self.toasts: list[str] = []
        self.button_presses: dict[str, bool] = {}
        self.form_submits: dict[str, bool] = {}
        self.selectbox_options: list[list[str]] = []
        self.reruns = 0
        self.toast = self._toast

    def header(self, _: str) -> None:
        return None

    def caption(self, _: str) -> None:
        return None

    def subheader(self, _: str) -> None:
        return None

    def write(self, _: str) -> None:
        return None

    def form(self, key: str, **_: object) -> FakeForm:
        self.forms.append(key)
        return FakeForm(self, key)

    def container(self, *, border: bool = False, **_: object) -> FakeContainer:
        self.container_borders.append(border)
        return FakeContainer(self)

    def text_input(self, _: str, *, value: str = "", key: str, **__: object) -> str:
        return str(self.session_state.get(key, value))

    def number_input(self, _: str, *, value, key: str, **__: object):
        return self.session_state.get(key, value)

    def selectbox(self, _: str, *, options, key: str, **__: object) -> str:
        normalized_options = list(options)
        self.selectbox_options.append(normalized_options)
        return str(self.session_state.get(key, normalized_options[0]))

    def form_submit_button(self, _: str, *, key: str | None = None, **__: object) -> bool:
        submit_key = key or self.forms[-1]
        return self.form_submits.get(submit_key, False)

    def button(self, _: str, *, key: str, **__: object) -> bool:
        return self.button_presses.get(key, False)

    def spinner(self, message: str) -> FakeContext:
        self.spinner_messages.append(message)
        return FakeContext(self, message)

    def success(self, message: str) -> None:
        self.successes.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def _toast(self, message: str, **__: object) -> None:
        self.toasts.append(message)

    def rerun(self) -> None:
        self.reruns += 1


def test_normalize_settings_form_strips_whitespace_from_model_name() -> None:
    normalized = normalize_settings_form(
        model="  openai/gpt-4o-mini  ",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        api_key="sk-demo",
        base_url=" https://api.example.test/v1/ ",
    )

    assert normalized["model"] == "openai/gpt-4o-mini"
    assert normalized["base_url"] == "https://api.example.test/v1"


def test_normalize_settings_form_strips_api_key_and_coerces_numbers() -> None:
    normalized = normalize_settings_form(
        model=" openai/gpt-4o-mini ",
        temperature="0.3",
        top_p="0.8",
        max_tokens="512",
        api_key=" sk-demo ",
        base_url=" https://api.example.test/v1/ ",
    )

    assert normalized == {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.3,
        "top_p": 0.8,
        "max_tokens": 512,
        "api_key": "sk-demo",
        "base_url": "https://api.example.test/v1",
        "theme_mode": "light",
    }


def test_fetch_available_models_builds_client_with_key_and_base_url() -> None:
    clients: list[FakeClient] = []
    connections: list[tuple[str, str]] = []

    def factory(api_key: str, base_url: str) -> FakeClient:
        connections.append((api_key, base_url))
        client = FakeClient(["zeta-model", "alpha-model"])
        clients.append(client)
        return client

    models = fetch_available_models(
        " sk-demo ",
        " https://api.example.test/v1/ ",
        factory,
    )

    assert models == ["zeta-model", "alpha-model"]
    assert connections == [("sk-demo", "https://api.example.test/v1")]
    assert clients[0].list_models_calls == 1


def test_save_settings_from_form_normalizes_and_calls_service() -> None:
    service = FakeSettingsService()

    normalized = save_settings_from_form(
        service,
        {
            "model": " openai/gpt-4o-mini ",
            "temperature": "0.3",
            "top_p": "0.8",
            "max_tokens": "512",
            "api_key": " sk-demo ",
            "base_url": " https://api.example.test/v1/ ",
        },
    )

    assert service.saved == [normalized]
    assert normalized == {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.3,
        "top_p": 0.8,
        "max_tokens": 512,
        "api_key": "sk-demo",
        "base_url": "https://api.example.test/v1",
        "theme_mode": "light",
    }


def test_build_settings_sections_returns_expected_groups() -> None:
    sections = build_settings_sections()

    assert [section["id"] for section in sections] == ["api", "model", "advanced"]


def test_render_settings_page_saves_through_single_grouped_form(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": " sk-demo ",
            "base_url": " https://api.example.test/v1/ ",
            "model": " openai/gpt-4o-mini ",
            "temperature": "0.3",
            "top_p": "0.8",
            "max_tokens": "512",
            "theme_mode": "dark",
        }
    )
    fake_st.form_submits["settings-form"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    service = FakeSettingsService()
    render_settings_page(
        settings={},
        settings_service=service,
    )

    assert fake_st.forms == ["settings-form"]
    assert len([border for border in fake_st.container_borders if border]) >= 3
    assert service.saved == [
        {
            "model": "openai/gpt-4o-mini",
            "temperature": 0.3,
            "top_p": 0.8,
            "max_tokens": 512,
            "api_key": "sk-demo",
            "base_url": "https://api.example.test/v1",
            "theme_mode": "dark",
        }
    ]


def test_render_settings_page_fetches_models_and_preselects_current_model(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": "sk-demo",
            "base_url": "https://api.example.test/v1",
            "model": "alpha-model",
        }
    )
    fake_st.form_submits["fetch_models"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_settings_page(
        settings={},
        client_factory=lambda _key, _url: FakeClient(["alpha-model", "zeta-model"]),
    )

    assert fake_st.spinner_messages == ["Проверяю сервис и загружаю модели..."]
    assert fake_st.toasts == ["Сервис доступен. Загружено моделей: 2."]
    assert fake_st.errors == []
    assert fake_st.session_state["available_models"] == ["alpha-model", "zeta-model"]
    assert fake_st.session_state["available_models_base_url"] == "https://api.example.test/v1"
    assert fake_st.session_state["model_from_catalog"] == "alpha-model"
    assert fake_st.reruns == 1


def test_render_settings_page_falls_back_to_success_when_toast_is_unavailable(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": "sk-demo",
            "base_url": "https://api.example.test/v1",
            "model": "alpha-model",
        }
    )
    fake_st.form_submits["fetch_models"] = True
    delattr(fake_st, "toast")

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_settings_page(
        settings={},
        client_factory=lambda _key, _url: FakeClient(["alpha-model"]),
    )

    assert fake_st.successes == ["Сервис доступен. Загружено моделей: 1."]


def test_render_settings_page_saves_model_selected_from_catalog(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": "sk-demo",
            "base_url": "https://api.example.test/v1",
            "available_models": ["alpha-model", "zeta-model"],
            "available_models_base_url": "https://api.example.test/v1",
            "model_from_catalog": "zeta-model",
            "temperature": 0.3,
            "top_p": 0.8,
            "max_tokens": 512,
            "theme_mode": "dark",
        }
    )
    fake_st.form_submits["settings-form"] = True
    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)
    service = FakeSettingsService()

    render_settings_page(settings={}, settings_service=service)

    assert fake_st.selectbox_options == [["alpha-model", "zeta-model"]]
    assert service.saved[0]["model"] == "zeta-model"
