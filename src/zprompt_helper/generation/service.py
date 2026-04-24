import json
from json import JSONDecodeError

import httpx

from zprompt_helper.openrouter.client import OpenRouterClient


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

            try:
                content = self._extract_content(response)
                parsed = json.loads(content)
                return self._validate_payload(parsed, active_blocks)
            except (JSONDecodeError, TypeError, KeyError, IndexError, ValueError):
                if validation_retry:
                    raise
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
        retry: bool,
    ) -> str:
        return json.dumps(
            {
                "short_idea": short_idea,
                "active_blocks": active_blocks,
                "block_instructions": block_instructions,
                "current_values": current_values,
                "locked_blocks": sorted(locked_blocks),
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

        return {block_id: str(payload[block_id]).strip() for block_id in active_blocks}

    @staticmethod
    def _extract_content(response: dict) -> str:
        return response["choices"][0]["message"]["content"]

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
