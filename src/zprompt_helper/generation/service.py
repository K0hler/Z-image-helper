import json
import re
from json import JSONDecodeError

import httpx

from zprompt_helper.openrouter.client import OpenRouterClient

_FENCE_RE = re.compile(
    r"^\s*```(?:json|JSON)?\s*\n?(?P<body>.*?)\n?```\s*$",
    re.DOTALL,
)
_CONTENT_SNIPPET_LIMIT = 200
_RESPONSE_DUMP_LIMIT = 600


class GenerationResponseError(ValueError):
    pass


class GenerationService:
    def __init__(self, client: OpenRouterClient) -> None:
        self.client = client

    def generate_blocks(
        self,
        model: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        short_idea: str,
        active_blocks: list[str],
        template_prompt: str,
        block_instructions: dict[str, str],
        current_values: dict[str, str],
        locked_blocks: set[str],
        regenerate_unlocked: bool = False,
        variation_index: int = 0,
        avoid_values: dict[str, str] | None = None,
    ) -> dict[str, str]:
        include_schema = True
        validation_retry = False

        while True:
            payload = self._build_payload(
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                short_idea=short_idea,
                active_blocks=active_blocks,
                template_prompt=template_prompt,
                block_instructions=block_instructions,
                current_values=current_values,
                locked_blocks=locked_blocks,
                regenerate_unlocked=regenerate_unlocked,
                variation_index=variation_index,
                avoid_values=avoid_values or {},
                include_schema=include_schema,
                retry=validation_retry,
            )

            try:
                response = self.client.create_chat_completion(payload)
            except httpx.HTTPStatusError as exc:
                if self._is_unsupported_response_format(exc, include_schema):
                    include_schema = False
                    continue
                raise

            content: str | None = None
            try:
                content = self._extract_content(response)
                parsed = json.loads(self._strip_code_fences(content))
                return self._validate_payload(parsed, active_blocks)
            except (JSONDecodeError, TypeError, KeyError, IndexError, ValueError) as exc:
                if include_schema and self._is_silent_empty_response(response):
                    include_schema = False
                    continue
                if validation_retry:
                    raise GenerationResponseError(
                        "Generation response stayed invalid after retry for blocks: "
                        f"{', '.join(active_blocks)}. Cause: {exc.__class__.__name__}: {exc}. "
                        f"Content: {self._content_snippet(content)}"
                    ) from exc
                validation_retry = True

    def _build_payload(
        self,
        model: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        short_idea: str,
        active_blocks: list[str],
        template_prompt: str,
        block_instructions: dict[str, str],
        current_values: dict[str, str],
        locked_blocks: set[str],
        regenerate_unlocked: bool,
        variation_index: int,
        avoid_values: dict[str, str],
        include_schema: bool,
        retry: bool,
    ) -> dict:
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "Return only valid JSON for the requested schema.",
                },
                {"role": "system", "content": template_prompt},
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        short_idea=short_idea,
                        active_blocks=active_blocks,
                        block_instructions=block_instructions,
                        current_values=current_values,
                        locked_blocks=locked_blocks,
                        regenerate_unlocked=regenerate_unlocked,
                        variation_index=variation_index,
                        avoid_values=avoid_values,
                        retry=retry,
                    ),
                },
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        if model:
            payload["model"] = model
        if include_schema:
            payload["response_format"] = self._build_response_format(active_blocks)
        return payload

    def _build_user_prompt(
        self,
        short_idea: str,
        active_blocks: list[str],
        block_instructions: dict[str, str],
        current_values: dict[str, str],
        locked_blocks: set[str],
        regenerate_unlocked: bool,
        variation_index: int,
        avoid_values: dict[str, str],
        retry: bool,
    ) -> str:
        return json.dumps(
            {
                "short_idea": short_idea,
                "active_blocks": active_blocks,
                "block_instructions": block_instructions,
                "current_values": current_values,
                "locked_blocks": sorted(locked_blocks),
                "regenerate_unlocked": regenerate_unlocked,
                "variation_index": variation_index,
                "avoid_values": avoid_values,
                "regeneration_rules": (
                    "For every unlocked block listed in avoid_values, return a materially different "
                    "alternative and do not repeat the same wording."
                    if regenerate_unlocked
                    else ""
                ),
                "retry": retry,
            },
            ensure_ascii=False,
        )

    def _build_response_format(self, active_blocks: list[str]) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "prompt_blocks",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        block_id: {"type": "string"} for block_id in active_blocks
                    },
                    "required": active_blocks,
                    "additionalProperties": False,
                },
            },
        }

    def _validate_payload(
        self,
        payload: object,
        active_blocks: list[str],
    ) -> dict[str, str]:
        if not isinstance(payload, dict):
            raise ValueError("Generation response must be a JSON object")

        missing = [block_id for block_id in active_blocks if block_id not in payload]
        extra = [block_id for block_id in payload if block_id not in active_blocks]
        if missing or extra:
            raise ValueError(f"Invalid block payload. missing={missing} extra={extra}")

        non_string = [
            block_id
            for block_id in active_blocks
            if not isinstance(payload[block_id], str)
        ]
        if non_string:
            raise ValueError(f"Invalid block value type. non_string={non_string}")

        return {block_id: payload[block_id].strip() for block_id in active_blocks}

    @staticmethod
    def _extract_content(response: dict) -> str:
        top_error = response.get("error") if isinstance(response, dict) else None
        if top_error:
            raise ValueError(f"OpenRouter returned an error in the response body: {top_error!r}")

        choices = response.get("choices") if isinstance(response, dict) else None
        if not choices:
            raise ValueError(
                "OpenRouter returned no choices. Full response: "
                f"{GenerationService._response_dump(response)}"
            )

        choice = choices[0]
        choice_error = choice.get("error") if isinstance(choice, dict) else None
        if choice_error:
            raise ValueError(f"Provider returned an error for this choice: {choice_error!r}")

        message = choice.get("message") or {}
        for field in ("content", "reasoning", "reasoning_content"):
            value = message.get(field)
            if isinstance(value, str) and value.strip():
                return value
        refusal = message.get("refusal")
        if isinstance(refusal, str) and refusal.strip():
            raise ValueError(f"Model refused to answer: {refusal}")
        finish_reason = choice.get("finish_reason")
        if finish_reason == "length":
            raise ValueError(
                "Model returned no textual content because output was cut off "
                "(finish_reason='length'). Increase max_tokens in Settings — "
                "reasoning models need substantially more (try 4000+)."
            )
        if finish_reason == "content_filter":
            raise ValueError(
                "Provider blocked the response via content filter "
                "(finish_reason='content_filter'). Try a different model or rephrase the idea."
            )
        completion_tokens = (
            response.get("usage", {}).get("completion_tokens")
            if isinstance(response, dict)
            else None
        )
        if completion_tokens == 0:
            provider = response.get("provider") if isinstance(response, dict) else None
            model_id = response.get("model") if isinstance(response, dict) else None
            raise ValueError(
                "Model produced 0 completion tokens — "
                f"provider {provider!r} on model {model_id!r} did not generate any output. "
                "This usually means the free/upstream provider is unavailable or rejected the prompt. "
                "Switch to a different model in Settings (e.g. openai/gpt-4o-mini, "
                "anthropic/claude-3.5-haiku, google/gemini-2.0-flash-exp)."
            )
        raise ValueError(
            "Model returned an empty response. Full OpenRouter response: "
            f"{GenerationService._response_dump(response)}"
        )

    @staticmethod
    def _response_dump(response: object) -> str:
        try:
            text = json.dumps(response, ensure_ascii=False)
        except (TypeError, ValueError):
            text = repr(response)
        if len(text) > _RESPONSE_DUMP_LIMIT:
            return text[:_RESPONSE_DUMP_LIMIT] + "…"
        return text

    @staticmethod
    def _strip_code_fences(content: str) -> str:
        if not isinstance(content, str):
            return content
        match = _FENCE_RE.match(content)
        if match:
            return match.group("body").strip()
        return content.strip()

    @staticmethod
    def _content_snippet(content: object) -> str:
        if content is None:
            return "<missing>"
        if not isinstance(content, str):
            return f"<{type(content).__name__}>"
        if not content:
            return "<empty>"
        if len(content) <= _CONTENT_SNIPPET_LIMIT:
            return repr(content)
        return repr(content[:_CONTENT_SNIPPET_LIMIT] + "…")

    @staticmethod
    def _is_unsupported_response_format(
        exc: httpx.HTTPStatusError,
        include_schema: bool,
    ) -> bool:
        return (
            include_schema
            and exc.response.status_code == 400
            and "response_format" in exc.response.text
        )

    @staticmethod
    def _is_silent_empty_response(response: object) -> bool:
        if not isinstance(response, dict):
            return False
        if response.get("error"):
            return False
        choices = response.get("choices") or []
        if not choices:
            return False
        choice = choices[0] if isinstance(choices[0], dict) else {}
        if choice.get("error"):
            return False
        message = choice.get("message") or {}
        for field in ("content", "reasoning", "reasoning_content", "refusal"):
            value = message.get(field)
            if isinstance(value, str) and value.strip():
                return False
        return True
