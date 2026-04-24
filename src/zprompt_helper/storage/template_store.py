import re
from pathlib import Path
from uuid import uuid4

from zprompt_helper.domain.models import TemplateDefinition
from zprompt_helper.storage.paths import ProjectPaths


_SAFE_TEMPLATE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


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
        self._validate_template_id(template.id)
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
        return [
            template.model_dump(mode="json")
            for template in self.load_all()
            if template.origin == "custom"
        ]

    def import_many(self, items: list[dict]) -> int:
        imported = 0
        existing_ids = {template.id for template in self.load_all()}

        for item in items:
            template = TemplateDefinition.model_validate(item)
            self._validate_template_id(template.id)
            if template.origin != "custom" or template.id in existing_ids:
                continue

            self.save(template)
            existing_ids.add(template.id)
            imported += 1

        return imported

    @staticmethod
    def _validate_template_id(template_id: str) -> None:
        if not _SAFE_TEMPLATE_ID.fullmatch(template_id):
            raise ValueError("template id must contain only ASCII letters, digits, underscores, and hyphens")
