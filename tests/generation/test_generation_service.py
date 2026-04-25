import json

import httpx
import pytest

from zprompt_helper.generation.service import GenerationResponseError, GenerationService
from zprompt_helper.openrouter.client import OpenRouterClient


def _service_with_handler(handler) -> GenerationService:
    http = httpx.Client(
        base_url="https://openrouter.ai/api/v1",
        transport=httpx.MockTransport(handler),
    )
    return GenerationService(OpenRouterClient(api_key="sk-demo", http=http))


def _generate(service: GenerationService, model: str = "openai/gpt-4o-mini") -> dict[str, str]:
    return service.generate_blocks(
        model=model,
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        short_idea="robot portrait",
        active_blocks=["subject", "style"],
        template_prompt="Template-specific rules",
        block_instructions={
            "subject": "Describe the subject",
            "style": "Describe the visual style",
        },
        current_values={"subject": "old robot"},
        locked_blocks={"style"},
        regenerate_unlocked=False,
        variation_index=0,
        avoid_values={},
    )


def test_generation_service_sends_json_schema_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers["authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"subject": " silver robot ", "style": " cinematic still "}
                            )
                        }
                    }
                ]
            },
        )

    service = _service_with_handler(handler)

    result = _generate(service)

    payload = captured["payload"]
    assert result == {"subject": "silver robot", "style": "cinematic still"}
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["authorization"] == "Bearer sk-demo"
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["temperature"] == 0.2
    assert payload["top_p"] == 0.9
    assert payload["max_tokens"] == 700
    assert payload["messages"][:2] == [
        {"role": "system", "content": "Return only valid JSON for the requested schema."},
        {"role": "system", "content": "Template-specific rules"},
    ]

    user_payload = json.loads(payload["messages"][2]["content"])
    assert user_payload == {
        "short_idea": "robot portrait",
        "active_blocks": ["subject", "style"],
        "block_instructions": {
            "subject": "Describe the subject",
            "style": "Describe the visual style",
        },
        "current_values": {"subject": "old robot"},
        "locked_blocks": ["style"],
        "regenerate_unlocked": False,
        "variation_index": 0,
        "avoid_values": {},
        "regeneration_rules": "",
        "retry": False,
    }
    assert payload["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "prompt_blocks",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "style": {"type": "string"},
                },
                "required": ["subject", "style"],
                "additionalProperties": False,
            },
        },
    }


def test_invalid_json_triggers_one_retry() -> None:
    calls: list[dict] = []
    responses = iter(
        [
            httpx.Response(200, json={"choices": [{"message": {"content": "not-json"}}]}),
            httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {"subject": "robot", "style": "cinematic"}
                                )
                            }
                        }
                    ]
                },
            ),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        return next(responses)

    service = _service_with_handler(handler)

    result = _generate(service)

    assert result == {"subject": "robot", "style": "cinematic"}
    assert [json.loads(call["messages"][2]["content"])["retry"] for call in calls] == [
        False,
        True,
    ]


def test_unsupported_response_format_falls_back_without_schema() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if len(calls) == 1:
            return httpx.Response(
                400,
                text="response_format is not supported for this model",
                request=request,
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"subject": "robot", "style": "cinematic"}
                            )
                        }
                    }
                ]
            },
        )

    service = _service_with_handler(handler)

    result = _generate(service)

    assert result == {"subject": "robot", "style": "cinematic"}
    assert "response_format" in calls[0]
    assert "response_format" not in calls[1]
    assert json.loads(calls[1]["messages"][2]["content"])["retry"] is False


def test_empty_model_is_omitted_from_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"subject": "robot", "style": "cinematic"}
                            )
                        }
                    }
                ]
            },
        )

    service = _service_with_handler(handler)

    result = _generate(service, model="")

    assert result == {"subject": "robot", "style": "cinematic"}
    assert "model" not in captured["payload"]


def test_extra_keys_retry_then_final_validation_error_if_still_invalid() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "subject": "robot",
                                    "style": "cinematic",
                                    "extra": "wrong",
                                }
                            )
                        }
                    }
                ]
            },
        )

    service = _service_with_handler(handler)

    with pytest.raises(GenerationResponseError, match="subject, style"):
        _generate(service)

    assert calls == 2


def test_non_string_block_values_trigger_retry_and_succeed_if_retry_returns_strings() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            content = {"subject": 123, "style": "cinematic"}
        else:
            content = {"subject": "robot", "style": "cinematic"}
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(content)}}]},
        )

    service = _service_with_handler(handler)

    result = _generate(service)

    assert result == {"subject": "robot", "style": "cinematic"}
    assert calls == 2


def test_permanently_invalid_json_raises_generation_response_error_after_two_calls() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    service = _service_with_handler(handler)

    with pytest.raises(GenerationResponseError, match="subject, style") as exc_info:
        _generate(service)

    assert calls == 2
    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)


def test_permanently_non_string_block_values_raise_generation_response_error() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"subject": ["robot"], "style": "cinematic"}
                            )
                        }
                    }
                ]
            },
        )

    service = _service_with_handler(handler)

    with pytest.raises(GenerationResponseError, match="subject, style"):
        _generate(service)

    assert calls == 2


def test_regenerate_payload_includes_variation_controls() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"subject": "new robot", "style": "cinematic"}
                            )
                        }
                    }
                ]
            },
        )

    service = _service_with_handler(handler)

    result = service.generate_blocks(
        model="openai/gpt-4o-mini",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        short_idea="robot portrait",
        active_blocks=["subject", "style"],
        template_prompt="Template-specific rules",
        block_instructions={
            "subject": "Describe the subject",
            "style": "Describe the visual style",
        },
        current_values={"subject": "old robot", "style": "cinematic"},
        locked_blocks={"style"},
        regenerate_unlocked=True,
        variation_index=3,
        avoid_values={"subject": "old robot"},
    )

    assert result == {"subject": "new robot", "style": "cinematic"}
    user_payload = json.loads(captured["payload"]["messages"][2]["content"])
    assert user_payload["regenerate_unlocked"] is True
    assert user_payload["variation_index"] == 3
    assert user_payload["avoid_values"] == {"subject": "old robot"}
    assert "materially different alternative" in user_payload["regeneration_rules"]
