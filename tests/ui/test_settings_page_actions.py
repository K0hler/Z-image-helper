from zprompt_helper.ui.settings_page import (
    normalize_settings_form,
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
