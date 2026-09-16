import httpx
import pytest

from zprompt_helper.openrouter.client import OpenRouterClient


def test_client_builds_http_client_with_custom_base_url(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_http = object()

    def build_http_client(**kwargs):
        captured.update(kwargs)
        return fake_http

    monkeypatch.setattr("zprompt_helper.openrouter.client.httpx.Client", build_http_client)

    client = OpenRouterClient("sk-demo", "https://api.example.test/v1/")

    assert client.http is fake_http
    assert captured == {
        "base_url": "https://api.example.test/v1/",
        "timeout": 30.0,
    }


def test_client_uses_custom_base_url_for_chat_completions() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        return httpx.Response(200, json={"choices": []})

    http = httpx.Client(
        base_url="https://api.example.test/v1/",
        transport=httpx.MockTransport(handler),
    )
    client = OpenRouterClient(
        api_key="sk-demo",
        base_url="https://api.example.test/v1",
        http=http,
    )

    client.create_chat_completion({"messages": []})

    assert captured == {
        "url": "https://api.example.test/v1/chat/completions",
        "authorization": "Bearer sk-demo",
    }


def test_list_models_reads_openai_compatible_response() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["Authorization"]
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "zeta-model", "object": "model"},
                    {"id": "alpha-model", "object": "model"},
                    {"object": "model"},
                ]
            },
        )

    http = httpx.Client(
        base_url="http://localhost:1234/v1/",
        transport=httpx.MockTransport(handler),
    )
    client = OpenRouterClient(
        api_key="local-key",
        base_url="http://localhost:1234/v1/",
        http=http,
    )

    models = client.list_models()

    assert models == ["alpha-model", "zeta-model"]
    assert captured == {
        "url": "http://localhost:1234/v1/models",
        "authorization": "Bearer local-key",
    }


def test_list_models_rejects_invalid_response_shape() -> None:
    http = httpx.Client(
        base_url="https://api.example.test/v1/",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"models": ["unexpected"]})
        ),
    )
    client = OpenRouterClient("sk-demo", "https://api.example.test/v1", http=http)

    with pytest.raises(ValueError, match="model list"):
        client.list_models()
