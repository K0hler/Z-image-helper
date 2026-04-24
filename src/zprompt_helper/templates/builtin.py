import json
from importlib.resources import files

from zprompt_helper.domain.models import TemplateDefinition


def load_builtin_templates() -> list[TemplateDefinition]:
    raw_text = files("zprompt_helper.assets").joinpath("builtin_templates.json").read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    return [TemplateDefinition.model_validate(item) for item in payload]
