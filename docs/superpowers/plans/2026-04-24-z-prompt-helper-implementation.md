# Z-Prompt-Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `v1` local Streamlit workbench defined in the PRD: built-in and custom prompt templates, OpenRouter-backed block generation with strict JSON validation, English prompt assembly, date-sharded history, and OS-backed API-key storage.

**Architecture:** Build a small Python package under `src/zprompt_helper` and keep `app.py` as a thin Streamlit entrypoint. Put domain models, storage, OpenRouter integration, and workbench state in separate modules so most behavior is covered by unit tests and the UI layer mostly wires services together. Store built-in templates as JSON assets, store user templates and history in `data/`, and store the API key only in the OS secret store.

**Tech Stack:** Python 3.12, Streamlit, Pydantic v2, httpx, keyring, pytest

---

## Preflight

If this folder still is not a git repository, initialize it before Task 1 so the commit steps work.

Run:

```bash
git init
```

Expected:

```text
Initialized empty Git repository
```

## Planned File Structure

- `pyproject.toml`: packaging, dependencies, pytest config.
- `.gitignore`: ignore runtime data, virtualenv, caches, local secrets.
- `app.py`: Streamlit entrypoint and top-level navigation.
- `src/zprompt_helper/__init__.py`: package version export.
- `src/zprompt_helper/domain/models.py`: Pydantic models for blocks, templates, settings, sessions, and history entries.
- `src/zprompt_helper/assets/builtin_templates.json`: 7 built-in templates shipped with the app.
- `src/zprompt_helper/templates/builtin.py`: loader for built-in templates from JSON assets.
- `src/zprompt_helper/storage/paths.py`: data directory resolution relative to the project root.
- `src/zprompt_helper/storage/template_store.py`: load, save, duplicate, import, export custom templates.
- `src/zprompt_helper/storage/history_store.py`: read, append, delete, clear, import, export history files by date.
- `src/zprompt_helper/storage/settings_store.py`: read and write non-secret settings JSON.
- `src/zprompt_helper/secrets/secret_store.py`: `keyring` adapter plus in-memory test double protocol.
- `src/zprompt_helper/services/settings_service.py`: combine settings JSON with secret-store API key.
- `src/zprompt_helper/workbench/session.py`: prompt assembly, block locking, and editor state transitions.
- `src/zprompt_helper/openrouter/client.py`: HTTP client for OpenRouter chat completions.
- `src/zprompt_helper/generation/service.py`: schema building, retry logic, JSON validation, and regeneration flow.
- `src/zprompt_helper/ui/workbench.py`: Workbench screen renderer.
- `src/zprompt_helper/ui/template_manager.py`: custom template management screen.
- `src/zprompt_helper/ui/settings_page.py`: settings screen renderer and validation action.
- `src/zprompt_helper/ui/history_panel.py`: reusable history section renderer.
- `tests/`: unit tests per module plus one app-shell smoke test.

## Implementation Decisions Resolved In This Plan

- Built-in templates are stored as JSON assets, not Python constants.
- The API key is stored with `keyring`, not in project-local JSON.
- The default model field is blank; if the user leaves it empty, requests omit `model` and let OpenRouter use the account default.
- The standard block catalog includes text-oriented blocks needed by `Text In Image`: `Headline`, `Subheadline`, `CTA`, and `Layout`.
- History import merges by entry `id`; if an imported `id` already exists, skip the duplicate entry.

### Task 1: Bootstrap The Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/zprompt_helper/__init__.py`
- Create: `tests/smoke/test_import.py`

- [ ] **Step 1: Write the failing smoke test**

```python
from importlib import import_module


def test_package_exposes_version() -> None:
    package = import_module("zprompt_helper")
    assert package.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/smoke/test_import.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper'
```

- [ ] **Step 3: Create package metadata and repo hygiene files**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "z-prompt-helper"
version = "0.1.0"
description = "Local prompt workbench for Z-Image Turbo"
requires-python = ">=3.12"
dependencies = [
  "streamlit>=1.44,<2.0",
  "httpx>=0.27,<1.0",
  "pydantic>=2.7,<3.0",
  "keyring>=25.2,<26.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2,<9.0",
  "pytest-cov>=5.0,<6.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```gitignore
.venv/
__pycache__/
.pytest_cache/
.coverage
htmlcov/
data/
```

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Install the package in editable mode**

Run:

```bash
python -m pip install -e .[dev]
```

Expected:

```text
Successfully installed z-prompt-helper
```

- [ ] **Step 5: Run the smoke test to verify it passes**

Run:

```bash
python -m pytest tests/smoke/test_import.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore src/zprompt_helper/__init__.py tests/smoke/test_import.py
git commit -m "chore: bootstrap python package"
```

### Task 2: Define Domain Models And Built-In Template Assets

**Files:**
- Create: `src/zprompt_helper/domain/models.py`
- Create: `src/zprompt_helper/assets/__init__.py`
- Create: `src/zprompt_helper/assets/builtin_templates.json`
- Create: `src/zprompt_helper/templates/builtin.py`
- Create: `tests/domain/test_builtin_templates.py`

- [ ] **Step 1: Write the failing built-in template test**

```python
from zprompt_helper.domain.models import BlockDefinition
from zprompt_helper.templates.builtin import load_builtin_templates


def test_builtin_catalog_contains_expected_templates() -> None:
    templates = load_builtin_templates()
    names = {template.name for template in templates}

    assert len(templates) == 7
    assert names == {
        "Universal",
        "Cinematic",
        "Photorealism",
        "Art / Illustration",
        "Character",
        "Scenes / Environment",
        "Text In Image",
    }
    assert all(template.origin == "built_in" for template in templates)


def test_text_in_image_template_contains_text_blocks() -> None:
    template = next(template for template in load_builtin_templates() if template.id == "text_in_image")

    assert set(template.blocks) >= {"headline", "subheadline", "cta", "layout"}
    assert isinstance(template.blocks["headline"], BlockDefinition)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/domain/test_builtin_templates.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.templates.builtin'
```

- [ ] **Step 3: Create the core domain models**

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BlockDefinition(BaseModel):
    id: str
    label: str
    instruction: str = ""
    enabled: bool = True


class TemplateDefinition(BaseModel):
    id: str
    name: str
    description: str
    origin: Literal["built_in", "custom"]
    block_order: list[str]
    blocks: dict[str, BlockDefinition]
    assembly_formula: str
    template_system_prompt: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

- [ ] **Step 4: Add the built-in template asset and loader**

```json
[
  {
    "id": "universal",
    "name": "Universal",
    "description": "Best general-purpose starter template.",
    "origin": "built_in",
    "block_order": ["subject", "scene", "composition", "lighting", "style", "details", "constraints"],
    "blocks": {
      "subject": {"id": "subject", "label": "Subject", "instruction": "Describe the main object and key details."},
      "scene": {"id": "scene", "label": "Scene", "instruction": "Describe where the subject exists and 1-2 environment details."}
    },
    "assembly_formula": "{subject}, {scene}, {composition}, {lighting}, {style}, {details}, {constraints}",
    "template_system_prompt": "Return only valid JSON matching the requested block schema."
  }
]
```

```python
import json
from importlib.resources import files

from zprompt_helper.domain.models import TemplateDefinition


def load_builtin_templates() -> list[TemplateDefinition]:
    raw_text = files("zprompt_helper.assets").joinpath("builtin_templates.json").read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    return [TemplateDefinition.model_validate(item) for item in payload]
```

```python
# src/zprompt_helper/assets/__init__.py
```

- [ ] **Step 5: Expand the JSON asset to the full 7-template set**

```json
{
  "id": "text_in_image",
  "name": "Text In Image",
  "description": "Graphic layouts with readable in-image text.",
  "origin": "built_in",
  "block_order": ["headline", "subheadline", "cta", "layout", "style", "details", "constraints"],
  "blocks": {
    "headline": {"id": "headline", "label": "Headline", "instruction": "Write the main on-image headline text."},
    "subheadline": {"id": "subheadline", "label": "Subheadline", "instruction": "Write the supporting text."},
    "cta": {"id": "cta", "label": "CTA", "instruction": "Write the short call-to-action text."},
    "layout": {"id": "layout", "label": "Layout", "instruction": "Describe text and image placement."},
    "style": {"id": "style", "label": "Style", "instruction": "Describe visual style and branding approach."},
    "details": {"id": "details", "label": "Details", "instruction": "Describe clarity, legibility, and render quality."},
    "constraints": {"id": "constraints", "label": "Constraints", "instruction": "State strict requirements such as no watermark or correct typography."}
  },
  "assembly_formula": "{headline}, {subheadline}, {cta}, {layout}, {style}, {details}, {constraints}",
  "template_system_prompt": "Return valid JSON and keep on-image text concise and readable."
}
```

- [ ] **Step 6: Run the test to verify it passes**

Run:

```bash
python -m pytest tests/domain/test_builtin_templates.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 7: Commit**

```bash
git add src/zprompt_helper/domain/models.py src/zprompt_helper/assets/__init__.py src/zprompt_helper/assets/builtin_templates.json src/zprompt_helper/templates/builtin.py tests/domain/test_builtin_templates.py
git commit -m "feat: add built-in template catalog"
```

### Task 3: Build Local Storage For Paths, Templates, And History

**Files:**
- Create: `src/zprompt_helper/storage/paths.py`
- Create: `src/zprompt_helper/storage/template_store.py`
- Create: `src/zprompt_helper/storage/history_store.py`
- Create: `tests/storage/test_history_store.py`
- Create: `tests/storage/test_template_store.py`

- [ ] **Step 1: Write the failing history sharding test**

```python
from datetime import UTC, datetime

from zprompt_helper.storage.history_store import HistoryStore
from zprompt_helper.storage.paths import ProjectPaths


def test_history_store_writes_entries_to_date_named_files(tmp_path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    store = HistoryStore(paths)

    entry = store.append(
        prompt_text="A cinematic still of a neon alley",
        created_at=datetime(2026, 4, 24, 10, 15, tzinfo=UTC),
    )

    history_file = tmp_path / "data" / "history" / "2026-04-24.json"
    assert history_file.exists()
    assert entry.prompt_text == "A cinematic still of a neon alley"
```

```python
from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.template_store import TemplateStore


def test_template_store_exports_and_imports_custom_templates(tmp_path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    store = TemplateStore(paths)
    template = TemplateDefinition(
        id="custom-universal",
        name="Custom Universal",
        description="editable",
        origin="custom",
        block_order=["subject"],
        blocks={"subject": BlockDefinition(id="subject", label="Subject")},
        assembly_formula="{subject}",
        template_system_prompt="Return JSON",
    )

    store.save(template)
    exported = store.export_all()

    assert exported[0]["id"] == "custom-universal"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/storage/test_history_store.py tests/storage/test_template_store.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.storage.history_store'
```

- [ ] **Step 3: Create the path resolver**

```python
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
```

- [ ] **Step 4: Create the custom template store**

```python
import json
from pathlib import Path
from uuid import uuid4

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.storage.paths import ProjectPaths


class TemplateStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def load_all(self) -> list[TemplateDefinition]:
        return [
            TemplateDefinition.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.paths.templates_dir.glob("*.json"))
        ]

    def save(self, template: TemplateDefinition) -> Path:
        target = self.paths.templates_dir / f"{template.id}.json"
        target.write_text(template.model_dump_json(indent=2), encoding="utf-8")
        return target

    def duplicate(self, template: TemplateDefinition, name: str) -> TemplateDefinition:
        clone = template.model_copy(deep=True)
        clone.id = f"{template.id}-{uuid4().hex[:8]}"
        clone.name = name
        clone.origin = "custom"
        return clone

    def export_all(self) -> list[dict]:
        return [template.model_dump(mode="json") for template in self.load_all()]

    def import_many(self, items: list[dict]) -> int:
        imported = 0
        existing_ids = {template.id for template in self.load_all()}
        for item in items:
            template = TemplateDefinition.model_validate(item)
            if template.origin != "custom" or template.id in existing_ids:
                continue
            self.save(template)
            existing_ids.add(template.id)
            imported += 1
        return imported
```

- [ ] **Step 5: Create the history store with date-based files**

```python
import json
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from zprompt_helper.storage.paths import ProjectPaths


class HistoryEntry(BaseModel):
    id: str
    prompt_text: str
    created_at: datetime


class HistoryStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths
        self.paths.ensure()

    def append(self, prompt_text: str, created_at: datetime | None = None) -> HistoryEntry:
        timestamp = created_at or datetime.now(UTC)
        entry = HistoryEntry(id=uuid4().hex, prompt_text=prompt_text, created_at=timestamp)
        target = self.paths.history_dir / f"{timestamp.date().isoformat()}.json"
        existing = json.loads(target.read_text(encoding="utf-8")) if target.exists() else []
        existing.append(entry.model_dump(mode="json"))
        target.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        return entry
```

- [ ] **Step 6: Add delete, clear, import, and export behavior with tests**

```python
def delete_entry(self, date_key: str, entry_id: str) -> None:
    target = self.paths.history_dir / f"{date_key}.json"
    entries = json.loads(target.read_text(encoding="utf-8"))
    kept = [item for item in entries if item["id"] != entry_id]
    target.write_text(json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8")

def clear_all(self) -> None:
    for path in self.paths.history_dir.glob("*.json"):
        path.unlink()

def export_all(self) -> list[dict]:
    payload: list[dict] = []
    for path in sorted(self.paths.history_dir.glob("*.json")):
        payload.extend(json.loads(path.read_text(encoding="utf-8")))
    return payload

def import_many(self, items: list[dict]) -> int:
    imported = 0
    seen = {entry["id"] for entry in self.export_all()}
    for item in items:
        if item["id"] in seen:
            continue
        self.append(prompt_text=item["prompt_text"], created_at=datetime.fromisoformat(item["created_at"]))
        imported += 1
    return imported
```

- [ ] **Step 7: Run tests to verify storage passes**

Run:

```bash
python -m pytest tests/storage/test_history_store.py tests/storage/test_template_store.py -v
```

Expected:

```text
4 passed
```

- [ ] **Step 8: Commit**

```bash
git add src/zprompt_helper/storage/paths.py src/zprompt_helper/storage/template_store.py src/zprompt_helper/storage/history_store.py tests/storage/test_history_store.py tests/storage/test_template_store.py
git commit -m "feat: add local template and history storage"
```

### Task 4: Add Settings Persistence And OS Secret Storage

**Files:**
- Create: `src/zprompt_helper/storage/settings_store.py`
- Create: `src/zprompt_helper/secrets/secret_store.py`
- Create: `src/zprompt_helper/services/settings_service.py`
- Create: `tests/services/test_settings_service.py`

- [ ] **Step 1: Write the failing settings service test**

```python
from zprompt_helper.services.settings_service import SettingsService
from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.storage.settings_store import SettingsStore
from zprompt_helper.secrets.secret_store import InMemorySecretStore


def test_settings_service_persists_api_key_outside_settings_json(tmp_path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    settings_store = SettingsStore(paths)
    secret_store = InMemorySecretStore()
    service = SettingsService(settings_store, secret_store)

    service.save(
        model="",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        api_key="sk-demo",
    )

    raw_json = (tmp_path / "data" / "settings.json").read_text(encoding="utf-8")
    assert "sk-demo" not in raw_json
    assert service.load().api_key == "sk-demo"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/services/test_settings_service.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.services.settings_service'
```

- [ ] **Step 3: Create non-secret settings storage**

```python
import json
from pydantic import BaseModel

from zprompt_helper.storage.paths import ProjectPaths


class SettingsPayload(BaseModel):
    model: str = ""
    temperature: float = 0.2
    top_p: float = 0.9
    max_tokens: int = 700


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
```

- [ ] **Step 4: Create the secret store adapter**

```python
from dataclasses import dataclass, field
from typing import Protocol

import keyring


SERVICE_NAME = "z-prompt-helper"
USERNAME = "openrouter-api-key"


class SecretStore(Protocol):
    def get_api_key(self) -> str:
        raise NotImplementedError

    def set_api_key(self, value: str) -> None:
        raise NotImplementedError


class KeyringSecretStore:
    def get_api_key(self) -> str:
        return keyring.get_password(SERVICE_NAME, USERNAME) or ""

    def set_api_key(self, value: str) -> None:
        keyring.set_password(SERVICE_NAME, USERNAME, value)


@dataclass
class InMemorySecretStore:
    value: str = field(default="")

    def get_api_key(self) -> str:
        return self.value

    def set_api_key(self, value: str) -> None:
        self.value = value
```

- [ ] **Step 5: Create the settings service that merges JSON settings with the API key**

```python
from dataclasses import dataclass

from zprompt_helper.secrets.secret_store import SecretStore
from zprompt_helper.storage.settings_store import SettingsPayload, SettingsStore


@dataclass
class AppSettings:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    api_key: str


class SettingsService:
    def __init__(self, store: SettingsStore, secrets: SecretStore) -> None:
        self.store = store
        self.secrets = secrets

    def load(self) -> AppSettings:
        payload = self.store.load()
        return AppSettings(
            model=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
            api_key=self.secrets.get_api_key(),
        )

    def save(self, model: str, temperature: float, top_p: float, max_tokens: int, api_key: str) -> None:
        self.store.save(SettingsPayload(model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens))
        if api_key:
            self.secrets.set_api_key(api_key)
```

- [ ] **Step 6: Run the test to verify it passes**

Run:

```bash
python -m pytest tests/services/test_settings_service.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 7: Commit**

```bash
git add src/zprompt_helper/storage/settings_store.py src/zprompt_helper/secrets/secret_store.py src/zprompt_helper/services/settings_service.py tests/services/test_settings_service.py
git commit -m "feat: add settings and secret storage"
```

### Task 5: Implement Workbench Session Rules And Prompt Assembly

**Files:**
- Create: `src/zprompt_helper/workbench/session.py`
- Create: `tests/workbench/test_session.py`

- [ ] **Step 1: Write the failing prompt assembly test**

```python
from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.workbench.session import EditorSession, rebuild_prompt


def test_rebuild_prompt_uses_template_formula_and_overwrites_manual_prompt() -> None:
    template = TemplateDefinition(
        id="universal",
        name="Universal",
        description="starter",
        origin="built_in",
        block_order=["subject", "style"],
        blocks={
            "subject": BlockDefinition(id="subject", label="Subject"),
            "style": BlockDefinition(id="style", label="Style"),
        },
        assembly_formula="{subject}, {style}",
        template_system_prompt="Return JSON",
    )
    session = EditorSession(
        short_idea="robot portrait",
        block_values={"subject": "portrait of a chrome robot", "style": "cinematic still"},
        final_prompt="manually edited prompt",
    )

    rebuilt = rebuild_prompt(template, session)
    assert rebuilt == "portrait of a chrome robot, cinematic still"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/workbench/test_session.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.workbench.session'
```

- [ ] **Step 3: Implement editor session and prompt assembly**

```python
from dataclasses import dataclass, field

from zprompt_helper.domain.models import TemplateDefinition


@dataclass
class EditorSession:
    short_idea: str = ""
    block_values: dict[str, str] = field(default_factory=dict)
    locked_blocks: set[str] = field(default_factory=set)
    final_prompt: str = ""


def rebuild_prompt(template: TemplateDefinition, session: EditorSession) -> str:
    values = {block_id: session.block_values.get(block_id, "") for block_id in template.block_order}
    return template.assembly_formula.format(**values).strip(", ")
```

- [ ] **Step 4: Add lock-aware state transitions**

```python
def merge_generated_blocks(
    session: EditorSession,
    generated_blocks: dict[str, str],
    block_ids: list[str],
) -> EditorSession:
    next_values = dict(session.block_values)
    for block_id in block_ids:
        if block_id in session.locked_blocks:
            continue
        if block_id in generated_blocks:
            next_values[block_id] = generated_blocks[block_id]
    session.block_values = next_values
    return session


def set_block_value(session: EditorSession, block_id: str, value: str) -> EditorSession:
    session.block_values[block_id] = value
    return session
```

- [ ] **Step 5: Expand tests for lock and regeneration rules**

```python
def test_merge_generated_blocks_skips_locked_fields() -> None:
    session = EditorSession(
        block_values={"style": "oil painting", "subject": "cat"},
        locked_blocks={"style"},
    )

    merge_generated_blocks(
        session,
        generated_blocks={"style": "photorealistic", "subject": "tiger"},
        block_ids=["subject", "style"],
    )

    assert session.block_values["style"] == "oil painting"
    assert session.block_values["subject"] == "tiger"
```

- [ ] **Step 6: Run the workbench tests to verify they pass**

Run:

```bash
python -m pytest tests/workbench/test_session.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 7: Commit**

```bash
git add src/zprompt_helper/workbench/session.py tests/workbench/test_session.py
git commit -m "feat: add workbench session rules"
```

### Task 6: Implement OpenRouter Client And Strict JSON Generation Service

**Files:**
- Create: `src/zprompt_helper/openrouter/client.py`
- Create: `src/zprompt_helper/generation/service.py`
- Create: `tests/generation/test_generation_service.py`

- [ ] **Step 1: Write the failing request-shape test**

```python
import httpx

from zprompt_helper.generation.service import GenerationService
from zprompt_helper.openrouter.client import OpenRouterClient


def test_generation_service_sends_json_schema_request(tmp_path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = request.content.decode("utf-8")
        return httpx.Response(200, json={"choices": [{"message": {"content": "{\"subject\":\"robot\"}"}}]})

    client = OpenRouterClient(api_key="sk-demo", http=httpx.Client(transport=httpx.MockTransport(handler)))
    service = GenerationService(client)

    service.generate_blocks(
        model="",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        short_idea="robot portrait",
        active_blocks=["subject"],
        template_prompt="Return JSON",
        block_instructions={"subject": "Describe the subject"},
        current_values={},
        locked_blocks=set(),
    )

    assert "\"response_format\"" in captured["json"]
```

- [ ] **Step 2: Run the generation test to verify it fails**

Run:

```bash
python -m pytest tests/generation/test_generation_service.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.generation.service'
```

- [ ] **Step 3: Implement the OpenRouter client**

```python
from collections.abc import Mapping
from typing import Any

import httpx


class OpenRouterClient:
    def __init__(self, api_key: str, http: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self.http = http or httpx.Client(base_url="https://openrouter.ai/api/v1", timeout=30.0)

    def create_chat_completion(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        response = self.http.post(
            "/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 4: Implement strict-schema generation with one retry**

```python
import json
import httpx


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
        payload = self._build_payload(model, temperature, top_p, max_tokens, short_idea, active_blocks, template_prompt, block_instructions, current_values, locked_blocks, include_schema=True)
        content = self._request_content(payload)
        try:
            return self._validate_payload(json.loads(content), active_blocks)
        except Exception:
            retry_payload = self._build_payload(model, temperature, top_p, max_tokens, short_idea, active_blocks, template_prompt, block_instructions, current_values, locked_blocks, include_schema=True, retry=True)
            retry_content = self._request_content(retry_payload)
            return self._validate_payload(json.loads(retry_content), active_blocks)

    def _request_content(self, payload: dict) -> str:
        try:
            response = self.client.create_chat_completion(payload)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400 and "response_format" in exc.response.text and payload.get("response_format"):
                fallback_payload = dict(payload)
                fallback_payload.pop("response_format", None)
                response = self.client.create_chat_completion(fallback_payload)
            else:
                raise
        return self._extract_content(response)

    @staticmethod
    def _extract_content(response: dict) -> str:
        return response["choices"][0]["message"]["content"]
```

- [ ] **Step 5: Add unsupported-structured-output fallback and validation helpers**

```python
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
    retry: bool = False,
) -> dict:
    messages = [
        {"role": "system", "content": "Return only valid JSON for the requested schema."},
        {"role": "system", "content": template_prompt},
        {"role": "user", "content": self._build_user_prompt(short_idea, active_blocks, block_instructions, current_values, locked_blocks, retry)},
    ]
    payload = {
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }
    if model:
        payload["model"] = model
    if include_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "prompt_blocks",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {block_id: {"type": "string"} for block_id in active_blocks},
                    "required": active_blocks,
                    "additionalProperties": False,
                },
            },
        }
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

def _validate_payload(self, payload: dict, active_blocks: list[str]) -> dict[str, str]:
    missing = [block_id for block_id in active_blocks if block_id not in payload]
    extra = [block_id for block_id in payload if block_id not in active_blocks]
    if missing or extra:
        raise ValueError(f"Invalid block payload. missing={missing} extra={extra}")
    return {block_id: str(payload[block_id]).strip() for block_id in active_blocks}
```

- [ ] **Step 6: Expand the tests for retry and structured-output fallback**

```python
def test_invalid_json_triggers_one_retry() -> None:
    responses = iter([
        httpx.Response(200, json={"choices": [{"message": {"content": "not-json"}}]}),
        httpx.Response(200, json={"choices": [{"message": {"content": "{\"subject\":\"robot\"}"}}]}),
    ])

    def handler(_: httpx.Request) -> httpx.Response:
        return next(responses)

    client = OpenRouterClient(api_key="sk-demo", http=httpx.Client(transport=httpx.MockTransport(handler)))
    service = GenerationService(client)

    result = service.generate_blocks(
        model="",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        short_idea="robot portrait",
        active_blocks=["subject"],
        template_prompt="Return JSON",
        block_instructions={"subject": "Describe the subject"},
        current_values={},
        locked_blocks=set(),
    )

    assert result == {"subject": "robot"}


def test_unsupported_response_format_falls_back_without_schema() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.content.decode("utf-8"))
        if len(calls) == 1:
            return httpx.Response(400, text="response_format is not supported for this model")
        return httpx.Response(200, json={"choices": [{"message": {"content": "{\"subject\":\"robot\"}"}}]})

    client = OpenRouterClient(api_key="sk-demo", http=httpx.Client(transport=httpx.MockTransport(handler)))
    service = GenerationService(client)

    result = service.generate_blocks(
        model="",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        short_idea="robot portrait",
        active_blocks=["subject"],
        template_prompt="Return JSON",
        block_instructions={"subject": "Describe the subject"},
        current_values={},
        locked_blocks=set(),
    )

    assert result == {"subject": "robot"}
    assert "\"response_format\"" in calls[0]
    assert "\"response_format\"" not in calls[1]
```

- [ ] **Step 7: Run the generation tests to verify they pass**

Run:

```bash
python -m pytest tests/generation/test_generation_service.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 8: Commit**

```bash
git add src/zprompt_helper/openrouter/client.py src/zprompt_helper/generation/service.py tests/generation/test_generation_service.py
git commit -m "feat: add openrouter generation flow"
```

### Task 7: Build The Streamlit Workbench Screen

**Files:**
- Create: `src/zprompt_helper/ui/workbench.py`
- Create: `tests/ui/test_workbench_actions.py`
- Modify: `app.py`

- [ ] **Step 1: Write the failing workbench action test**

```python
from zprompt_helper.ui.workbench import apply_generated_result
from zprompt_helper.workbench.session import EditorSession


def test_apply_generated_result_rebuilds_the_final_prompt() -> None:
    session = EditorSession(block_values={"subject": "robot"})
    next_session = apply_generated_result(
        session=session,
        generated_blocks={"style": "cinematic still"},
        block_ids=["subject", "style"],
        formula="{subject}, {style}",
    )

    assert next_session.final_prompt == "robot, cinematic still"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/ui/test_workbench_actions.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.ui.workbench'
```

- [ ] **Step 3: Implement testable workbench action helpers**

```python
from zprompt_helper.workbench.session import EditorSession, merge_generated_blocks


def apply_generated_result(
    session: EditorSession,
    generated_blocks: dict[str, str],
    block_ids: list[str],
    formula: str,
) -> EditorSession:
    updated = merge_generated_blocks(session, generated_blocks, block_ids)
    values = {block_id: updated.block_values.get(block_id, "") for block_id in block_ids}
    updated.final_prompt = formula.format(**values).strip(", ")
    return updated
```

- [ ] **Step 4: Create the Streamlit workbench renderer**

```python
import streamlit as st


def render_workbench(view_model: dict) -> None:
    st.title("Z-Prompt-Helper")
    st.selectbox("Шаблон", options=view_model["template_names"], key="selected_template_id")
    st.text_area("Кратко о том, что хотите создать", key="short_idea", height=100)
    col1, col2, col3 = st.columns(3)
    col1.button("Сгенерировать", key="generate")
    col2.button("Перегенерировать незаблокированные", key="regenerate_unlocked")
    col3.button("Скопировать промт", key="copy_prompt")
```

- [ ] **Step 5: Wire the top-level app shell**

```python
from pathlib import Path

import streamlit as st

from zprompt_helper.storage.paths import ProjectPaths
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.workbench import render_workbench


ROOT = Path(__file__).resolve().parent


def main() -> None:
    st.set_page_config(page_title="Z-Prompt-Helper", layout="wide")
    paths = ProjectPaths.from_root(ROOT)
    templates = load_builtin_templates()
    render_workbench({"template_names": [template.name for template in templates], "paths": paths})


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests and a manual smoke launch**

Run:

```bash
python -m pytest tests/ui/test_workbench_actions.py -v
streamlit run app.py
```

Expected:

```text
1 passed
You can now view your Streamlit app in your browser.
```

- [ ] **Step 7: Commit**

```bash
git add app.py src/zprompt_helper/ui/workbench.py tests/ui/test_workbench_actions.py
git commit -m "feat: add workbench screen"
```

### Task 8: Build Template Manager With Custom Copy Editing And Import/Export

**Files:**
- Create: `src/zprompt_helper/ui/template_manager.py`
- Create: `tests/ui/test_template_manager_actions.py`
- Modify: `app.py`

- [ ] **Step 1: Write the failing duplicate-template test**

```python
from zprompt_helper.domain.models import BlockDefinition, TemplateDefinition
from zprompt_helper.ui.template_manager import build_custom_copy


def test_build_custom_copy_marks_template_as_custom() -> None:
    original = TemplateDefinition(
        id="cinematic",
        name="Cinematic",
        description="film look",
        origin="built_in",
        block_order=["subject"],
        blocks={"subject": BlockDefinition(id="subject", label="Subject")},
        assembly_formula="{subject}",
        template_system_prompt="Return JSON",
    )

    duplicated = build_custom_copy(original)
    assert duplicated.origin == "custom"
    assert duplicated.id != original.id
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/ui/test_template_manager_actions.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.ui.template_manager'
```

- [ ] **Step 3: Implement copy and edit helpers for custom templates**

```python
from datetime import UTC, datetime
from uuid import uuid4

from zprompt_helper.domain.models import TemplateDefinition


def build_custom_copy(template: TemplateDefinition) -> TemplateDefinition:
    duplicate = template.model_copy(deep=True)
    duplicate.id = f"{template.id}-{uuid4().hex[:8]}"
    duplicate.name = f"{template.name} Copy"
    duplicate.origin = "custom"
    duplicate.created_at = datetime.now(UTC)
    duplicate.updated_at = datetime.now(UTC)
    return duplicate
```

- [ ] **Step 4: Create the Streamlit template manager screen**

```python
import streamlit as st


def render_template_manager(custom_templates: list, built_in_templates: list) -> None:
    st.header("Шаблоны")
    st.subheader("Встроенные")
    for template in built_in_templates:
        st.button(f"Создать копию: {template.name}", key=f"copy-{template.id}")

    st.subheader("Пользовательские")
    for template in custom_templates:
        with st.expander(template.name):
            st.text_input("Название", value=template.name, key=f"name-{template.id}")
            st.text_area("Системный промт шаблона", value=template.template_system_prompt, key=f"system-{template.id}")
            st.text_area("Формула сборки", value=template.assembly_formula, key=f"formula-{template.id}")
```

- [ ] **Step 5: Add import/export buttons and route from `app.py`**

```python
from zprompt_helper.storage.template_store import TemplateStore
from zprompt_helper.templates.builtin import load_builtin_templates


built_in_templates = load_builtin_templates()
custom_templates = TemplateStore(paths).load_all()
page = st.sidebar.radio("Раздел", options=["Workbench", "Template Manager"])

if page == "Workbench":
    template_names = [template.name for template in [*built_in_templates, *custom_templates]]
    render_workbench({"template_names": template_names})
else:
    render_template_manager(custom_templates, built_in_templates)
```

- [ ] **Step 6: Run tests and do a manual workflow check**

Run:

```bash
python -m pytest tests/ui/test_template_manager_actions.py -v
streamlit run app.py
```

Expected:

```text
1 passed
Template Manager is reachable from the sidebar and built-in templates offer a "Создать копию" action.
```

- [ ] **Step 7: Commit**

```bash
git add app.py src/zprompt_helper/ui/template_manager.py tests/ui/test_template_manager_actions.py
git commit -m "feat: add template manager"
```

### Task 9: Add Settings Screen, History Panel, And End-To-End Wiring

**Files:**
- Create: `src/zprompt_helper/ui/settings_page.py`
- Create: `src/zprompt_helper/ui/history_panel.py`
- Create: `tests/ui/test_settings_page_actions.py`
- Create: `tests/ui/test_history_panel.py`
- Modify: `app.py`
- Modify: `src/zprompt_helper/ui/workbench.py`

- [ ] **Step 1: Write the failing settings validation test**

```python
from zprompt_helper.ui.settings_page import normalize_settings_form


def test_normalize_settings_form_strips_whitespace_from_model_name() -> None:
    normalized = normalize_settings_form(
        model="  openai/gpt-4o-mini  ",
        temperature=0.2,
        top_p=0.9,
        max_tokens=700,
        api_key="sk-demo",
    )

    assert normalized["model"] == "openai/gpt-4o-mini"
```

```python
from zprompt_helper.ui.history_panel import summarize_history_entries


def test_summarize_history_entries_returns_latest_first() -> None:
    items = [
        {"id": "1", "prompt_text": "first", "created_at": "2026-04-24T10:00:00+00:00"},
        {"id": "2", "prompt_text": "second", "created_at": "2026-04-24T12:00:00+00:00"},
    ]

    summary = summarize_history_entries(items)
    assert summary[0]["id"] == "2"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/ui/test_settings_page_actions.py tests/ui/test_history_panel.py -v
```

Expected:

```text
E   ModuleNotFoundError: No module named 'zprompt_helper.ui.settings_page'
```

- [ ] **Step 3: Implement settings helpers and the settings screen**

```python
import streamlit as st

from zprompt_helper.openrouter.client import OpenRouterClient


def normalize_settings_form(model: str, temperature: float, top_p: float, max_tokens: int, api_key: str) -> dict:
    return {
        "model": model.strip(),
        "temperature": float(temperature),
        "top_p": float(top_p),
        "max_tokens": int(max_tokens),
        "api_key": api_key.strip(),
    }

def validate_connection(client: OpenRouterClient, model: str) -> bool:
    payload = {
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    if model:
        payload["model"] = model
    response = client.create_chat_completion(payload)
    return bool(response.get("choices"))


def render_settings_page(settings: dict) -> None:
    st.header("Настройки")
    st.text_input("OpenRouter API Key", value=settings.get("api_key", ""), type="password", key="api_key")
    st.text_input("Модель", value=settings.get("model", ""), key="model")
    st.number_input("Temperature", min_value=0.0, max_value=2.0, value=float(settings.get("temperature", 0.2)), key="temperature")
    st.number_input("Top P", min_value=0.0, max_value=1.0, value=float(settings.get("top_p", 0.9)), key="top_p")
    st.number_input("Max tokens", min_value=1, max_value=4096, value=int(settings.get("max_tokens", 700)), key="max_tokens")
    st.button("Сохранить", key="save_settings")
    st.button("Проверить ключ", key="validate_api_key")
```

- [ ] **Step 4: Implement the reusable history panel**

```python
import streamlit as st


def summarize_history_entries(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=lambda item: item["created_at"], reverse=True)


def render_history_panel(entries: list[dict]) -> None:
    st.subheader("История")
    for entry in summarize_history_entries(entries):
        with st.expander(entry["created_at"]):
            st.code(entry["prompt_text"])
            st.button("Скопировать", key=f"copy-history-{entry['id']}")
            st.button("Удалить", key=f"delete-history-{entry['id']}")
    st.button("Очистить историю", key="clear_history")
```

- [ ] **Step 5: Wire settings and history into the app shell**

```python
from zprompt_helper.secrets.secret_store import KeyringSecretStore
from zprompt_helper.services.settings_service import SettingsService
from zprompt_helper.storage.history_store import HistoryStore
from zprompt_helper.storage.settings_store import SettingsStore
from zprompt_helper.storage.template_store import TemplateStore
from zprompt_helper.templates.builtin import load_builtin_templates
from zprompt_helper.ui.history_panel import render_history_panel
from zprompt_helper.ui.settings_page import render_settings_page
from zprompt_helper.ui.template_manager import render_template_manager


settings_service = SettingsService(SettingsStore(paths), KeyringSecretStore())
history_entries = HistoryStore(paths).export_all()
custom_templates = TemplateStore(paths).load_all()
built_in_templates = load_builtin_templates()
settings_vm = settings_service.load().__dict__
page = st.sidebar.radio("Раздел", options=["Workbench", "Template Manager", "Settings"])

if page == "Workbench":
    template_names = [template.name for template in [*built_in_templates, *custom_templates]]
    render_workbench({"template_names": template_names})
    render_history_panel(history_entries)
elif page == "Template Manager":
    render_template_manager(custom_templates, built_in_templates)
else:
    render_settings_page(settings_vm)
```

- [ ] **Step 6: Run the full test suite and final manual acceptance**

Run:

```bash
python -m pytest -v
streamlit run app.py
```

Expected:

```text
All tests pass.
Workbench, Template Manager, and Settings are reachable.
Generating, editing, copying, history append/delete, template duplication, and settings save all work manually.
```

- [ ] **Step 7: Commit**

```bash
git add app.py src/zprompt_helper/ui/settings_page.py src/zprompt_helper/ui/history_panel.py src/zprompt_helper/ui/workbench.py tests/ui/test_settings_page_actions.py tests/ui/test_history_panel.py
git commit -m "feat: finish app wiring and settings flow"
```

## Spec Coverage Check

- Product shape and editor-first workflow: covered by Tasks 7-9.
- Built-in templates and custom copies: covered by Tasks 2, 3, and 8.
- Strict JSON generation and retry rules: covered by Task 6.
- Block locking and prompt rebuild rules: covered by Task 5.
- History by date and separate import/export: covered by Task 3 and UI wiring in Task 9.
- OS secret storage for API key: covered by Task 4.
- Settings, model parameters, and validation entrypoint: covered by Tasks 4 and 9.

## Placeholder Scan

No `TODO`, `TBD`, or deferred implementation placeholders are allowed during execution. If an executor discovers an unexpected dependency, they must add a concrete task update before coding around it.

## Type Consistency Check

- Template origin uses only `built_in` and `custom`.
- History entries merge by `id`.
- Final prompt assembly always uses `assembly_formula`.
- The default model is an empty string, not a fake placeholder model.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-24-z-prompt-helper-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
