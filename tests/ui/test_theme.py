from zprompt_helper.ui.theme import ThemeTokens, build_theme_css, normalize_theme_mode


def test_build_theme_css_contains_core_tokens() -> None:
    css = build_theme_css(ThemeTokens())

    assert "--zp-surface" in css
    assert "Manrope" in css
    assert "IBM Plex Mono" in css


def test_build_theme_css_supports_dark_mode_tokens() -> None:
    css = build_theme_css(theme_mode="dark")

    assert "#101318" in css
    assert "rgba(23, 28, 34, 0.84)" in css
    assert ".st-key-theme_toggle button::before" in css
    assert '[data-testid="stTextArea"] textarea' in css
    assert ".zp-status-chip--accent" in css
    assert 'content: "☾"' in css


def test_normalize_theme_mode_defaults_to_light() -> None:
    assert normalize_theme_mode("unknown") == "light"
    assert normalize_theme_mode("dark") == "dark"
