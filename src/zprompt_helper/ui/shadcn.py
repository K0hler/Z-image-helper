from collections.abc import Iterable, Sequence
from contextlib import nullcontext
from typing import Any


def shadcn_available() -> bool:
    try:
        import streamlit_shadcn_ui  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def normalize_nav_items(items: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for item in items:
        item_id = str(item["id"]).strip()
        label = str(item["label"]).strip()
        if not item_id or not label or item_id in seen_ids:
            continue
        normalized.append({"id": item_id, "label": label})
        seen_ids.add(item_id)

    return normalized


def section_card(st_module: Any, *, title: str | None = None, description: str | None = None):
    container = _safe_container(st_module, border=True)
    if title:
        getattr(st_module, "subheader", lambda *_args, **_kwargs: None)(title)
    if description:
        getattr(st_module, "caption", lambda *_args, **_kwargs: None)(description)
    return container


def badge(st_module: Any, label: str, *, color: str = "gray", icon: str | None = None) -> None:
    badge_fn = getattr(st_module, "badge", None)
    if callable(badge_fn):
        kwargs = {"color": color}
        if icon:
            kwargs["icon"] = icon
        badge_fn(label, **kwargs)
        return
    write_fn = getattr(st_module, "write", None)
    if callable(write_fn):
        icon_prefix = f"{icon} " if icon else ""
        write_fn(f"{icon_prefix}{label}")


def render_tabs(st_module: Any, labels: Sequence[str]) -> list[Any]:
    tabs_fn = getattr(st_module, "tabs", None)
    if callable(tabs_fn):
        return list(tabs_fn(list(labels)))
    return [nullcontext() for _ in labels]


def _safe_container(st_module: Any, **kwargs: object):
    container_fn = getattr(st_module, "container", None)
    if callable(container_fn):
        try:
            return container_fn(**kwargs)
        except TypeError:
            return container_fn()
    return nullcontext()
