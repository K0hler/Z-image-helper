from typing import Literal

from pydantic import BaseModel

from zprompt_helper.storage.paths import ProjectPaths


class SettingsPayload(BaseModel):
    model: str = ""
    temperature: float = 0.2
    top_p: float = 0.9
    max_tokens: int = 700
    theme_mode: Literal["light", "dark"] = "light"


class SettingsStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()
        self.target = self.paths.data_dir / "settings.json"

    def load(self) -> SettingsPayload:
        if not self.target.exists():
            return SettingsPayload()
        return SettingsPayload.model_validate_json(self.target.read_text(encoding="utf-8"))

    def save(self, payload: SettingsPayload) -> None:
        self.target.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
