from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data_dir: Path
    templates_dir: Path
    history_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        data_dir = root / "data"
        return cls(
            root=root,
            data_dir=data_dir,
            templates_dir=data_dir / "templates",
            history_dir=data_dir / "history",
        )

    def ensure(self) -> None:
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
