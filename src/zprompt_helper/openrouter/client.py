import httpx


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("Base URL is required")
    return normalized


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        http: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = normalize_base_url(base_url)
        self.http = http or httpx.Client(
            base_url=f"{self.base_url}/",
            timeout=30.0,
        )

    def create_chat_completion(self, payload: dict) -> dict:
        response = self.http.post(
            "chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        return response.json()

    def list_models(self) -> list[str]:
        response = self.http.get(
            "models",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise ValueError("API returned an invalid model list")

        model_ids = {
            str(item.get("id", "")).strip()
            for item in data
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        }
        if not model_ids:
            raise ValueError("API returned an empty model list")
        return sorted(model_ids, key=str.casefold)
