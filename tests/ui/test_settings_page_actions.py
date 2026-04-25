from zprompt_helper.ui.settings_page import (
    build_settings_sections,
    normalize_settings_form,
    render_settings_page,
    save_settings_from_form,
    validate_connection,
    validate_settings_connection,
)


class FakeClient:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def create_chat_completion(self, payload: dict) -> dict:
        self.payloads.append(payload)
        return {"choices": [{"message": {"content": "ok"}}]}


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


def test_normalize_settings_form_strips_whitespace_from_model_name() -> None:
    normalized = normalize_settings_form(
        model="  openai/gpt-4o-mini  ",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        api_key="sk-demo",
    )

    assert normalized["model"] == "openai/gpt-4o-mini"


def test_normalize_settings_form_strips_api_key_and_coerces_numbers() -> None:
    normalized = normalize_settings_form(
        model=" openai/gpt-4o-mini ",
        temperature="0.3",
        top_p="0.8",
        max_tokens="512",
        api_key=" sk-demo ",
    )

    assert normalized == {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.3,
        "top_p": 0.8,
        "max_tokens": 512,
        "api_key": "sk-demo",
        "theme_mode": "light",
    }


def test_validate_connection_omits_model_when_blank() -> None:
    client = FakeClient()

    assert validate_connection(client, "  ") is True
    assert "model" not in client.payloads[0]


def test_validate_connection_includes_model_when_set() -> None:
    client = FakeClient()

    assert validate_connection(client, "openai/gpt-4o-mini") is True
    assert client.payloads[0]["model"] == "openai/gpt-4o-mini"


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
        },
    )

    assert service.saved == [normalized]
    assert normalized == {
        "model": "openai/gpt-4o-mini",
        "temperature": 0.3,
        "top_p": 0.8,
        "max_tokens": 512,
        "api_key": "sk-demo",
        "theme_mode": "light",
    }


def test_validate_settings_connection_builds_client_with_api_key() -> None:
    clients: list[FakeClient] = []
    keys: list[str] = []

    def factory(api_key: str) -> FakeClient:
        keys.append(api_key)
        client = FakeClient()
        clients.append(client)
        return client

    assert validate_settings_connection(" sk-demo ", "openai/gpt-4o-mini", factory)
    assert keys == ["sk-demo"]
    assert clients[0].payloads[0]["model"] == "openai/gpt-4o-mini"


def test_build_settings_sections_returns_expected_groups() -> None:
    sections = build_settings_sections()

    assert [section["id"] for section in sections] == ["api", "model", "advanced"]


def test_render_settings_page_saves_through_single_grouped_form(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": " sk-demo ",
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
            "theme_mode": "dark",
        }
    ]


def test_render_settings_page_uses_spinner_and_transient_feedback_for_validation(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": "sk-demo",
            "model": "openai/gpt-4o-mini",
        }
    )
    fake_st.button_presses["validate_api_key"] = True

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_settings_page(
        settings={},
        client_factory=lambda _: FakeClient(),
    )

    assert fake_st.spinner_messages == ["Validating OpenRouter key..."]
    assert fake_st.toasts == ["OpenRouter connection works."]
    assert fake_st.errors == []


def test_render_settings_page_falls_back_to_success_when_toast_is_unavailable(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "api_key": "sk-demo",
            "model": "openai/gpt-4o-mini",
        }
    )
    fake_st.button_presses["validate_api_key"] = True
    delattr(fake_st, "toast")

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_st)

    render_settings_page(
        settings={},
        client_factory=lambda _: FakeClient(),
    )

    assert fake_st.successes == ["OpenRouter connection works."]
