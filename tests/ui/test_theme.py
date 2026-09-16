from zprompt_helper.ui.theme import ThemeTokens, build_theme_css, normalize_theme_mode


def test_build_theme_css_contains_core_tokens() -> None:
    css = build_theme_css(ThemeTokens())

    assert "--zp-surface" in css
    assert "--zp-accent" in css
    assert ".st-key-workbench_composer_panel" in css
    assert "border-radius: 16px" in css
    assert "Manrope" in css
    assert "IBM Plex Mono" in css


def test_build_theme_css_supports_dark_mode_tokens() -> None:
    css = build_theme_css(theme_mode="dark")

    assert "#111214" in css
    assert "#191b1f" in css
    assert "#5f636d" in css
    assert "#79a887" not in css
    assert ".st-key-theme_toggle button" in css
    assert '[data-testid="stTextArea"] textarea' in css
    assert ".st-key-workbench_output_panel" in css
    assert "position: sticky" in css


def test_dark_theme_overrides_native_light_widget_surfaces() -> None:
    css = build_theme_css(theme_mode="dark")

    assert '[data-testid="stTextArea"] [data-baseweb="base-input"]' in css
    assert '[data-testid="stSelectbox"] [data-baseweb="select"] > div *' in css
    assert '[data-testid="stExpander"] details[open] > summary' in css
    assert "-webkit-text-fill-color: var(--zp-ink) !important" in css


def test_build_theme_css_styles_idea_history_rows_as_menu_items() -> None:
    css = build_theme_css(theme_mode="dark")

    assert '[class*="st-key-use-idea-history-"] button' in css
    assert "justify-content: flex-start !important" in css
    assert "text-align: left !important" in css


def test_dark_theme_styles_selectbox_popover_layers() -> None:
    css = build_theme_css(theme_mode="dark")

    assert '[data-baseweb="popover"] > div' in css
    assert '[data-baseweb="popover"] ul' in css
    assert '[role="option"][aria-selected="true"] > div' in css
    assert '[role="option"]:hover > div' in css


def test_normalize_theme_mode_defaults_to_light() -> None:
    assert normalize_theme_mode("unknown") == "light"
    assert normalize_theme_mode("dark") == "dark"
