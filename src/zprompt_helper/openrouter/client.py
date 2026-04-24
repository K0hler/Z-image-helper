import httpx


class OpenRouterClient:
    def __init__(self, api_key: str, http: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self.http = http or httpx.Client(
            base_url="https://openrouter.ai/api/v1",
            timeout=30.0,
        )

    def create_chat_completion(self, payload: dict) -> dict:
        response = self.http.post(
            "/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        return response.json()
