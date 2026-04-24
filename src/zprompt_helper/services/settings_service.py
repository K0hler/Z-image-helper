from dataclasses import dataclass

from zprompt_helper.secrets.secret_store import SecretStore
from zprompt_helper.storage.settings_store import SettingsPayload, SettingsStore


@dataclass(frozen=True)
class AppSettings:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    api_key: str


class SettingsService:
    def __init__(self, settings_store: SettingsStore, secrets: SecretStore) -> None:
        self.settings_store = settings_store
        self.secrets = secrets

    def load(self) -> AppSettings:
        payload = self.settings_store.load()
        return AppSettings(
            model=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
            api_key=self.secrets.get_api_key(),
        )

    def save(
        self,
        model: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        api_key: str,
    ) -> None:
        self.settings_store.save(
            SettingsPayload(
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
        )
        if api_key:
            self.secrets.set_api_key(api_key)
