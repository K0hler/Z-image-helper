from dataclasses import dataclass
from typing import Literal

from zprompt_helper.secrets.secret_store import SecretStore
from zprompt_helper.storage.settings_store import SettingsPayload, SettingsStore


@dataclass(frozen=True)
class AppSettings:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    api_key: str
    theme_mode: Literal["light", "dark"]


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
            theme_mode=payload.theme_mode,
        )

    def save(
        self,
        model: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        api_key: str,
        theme_mode: Literal["light", "dark"] = "light",
    ) -> None:
        self.settings_store.save(
            SettingsPayload(
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                theme_mode=theme_mode,
            )
        )
        if api_key:
            self.secrets.set_api_key(api_key)

    def save_theme_mode(self, theme_mode: Literal["light", "dark"]) -> None:
        current = self.settings_store.load()
        self.settings_store.save(
            SettingsPayload(
                model=current.model,
                temperature=current.temperature,
                top_p=current.top_p,
                max_tokens=current.max_tokens,
                theme_mode=theme_mode,
            )
        )
