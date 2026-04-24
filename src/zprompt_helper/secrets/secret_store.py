from dataclasses import dataclass
from typing import Protocol

import keyring


SERVICE_NAME = "z-prompt-helper"
USERNAME = "openrouter-api-key"


class SecretStore(Protocol):
    def get_api_key(self) -> str:
        ...

    def set_api_key(self, value: str) -> None:
        ...


class KeyringSecretStore:
    def get_api_key(self) -> str:
        return keyring.get_password(SERVICE_NAME, USERNAME) or ""

    def set_api_key(self, value: str) -> None:
        keyring.set_password(SERVICE_NAME, USERNAME, value)


@dataclass
class InMemorySecretStore:
    api_key: str = ""

    def get_api_key(self) -> str:
        return self.api_key

    def set_api_key(self, value: str) -> None:
        self.api_key = value
