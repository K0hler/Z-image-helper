from zprompt_helper.ui.shadcn import normalize_nav_items, shadcn_available


def test_normalize_nav_items_keeps_declared_order() -> None:
    items = normalize_nav_items(
        [
            {"id": "workbench", "label": "Workbench"},
            {"id": "template_manager", "label": "Template Manager"},
            {"id": "settings", "label": "Settings"},
        ]
    )

    assert [item["id"] for item in items] == ["workbench", "template_manager", "settings"]


def test_shadcn_available_returns_bool() -> None:
    assert isinstance(shadcn_available(), bool)
