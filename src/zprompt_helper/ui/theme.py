from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ThemeTokens:
    canvas: str = "#f5efe6"
    surface: str = "#fffaf3"
    surface_alt: str = "#f0e6d8"
    ink: str = "#201a17"
    muted: str = "#6e6258"
    accent: str = "#a35b2f"
    accent_soft: str = "#ead3bf"
    border: str = "#dbcbbc"
    success: str = "#2f6f4f"
    danger: str = "#9b3d2f"


LIGHT_TOKENS = ThemeTokens(
    canvas="#f5efe6",
    surface="#fffaf3",
    surface_alt="#f0e6d8",
    ink="#201a17",
    muted="#6e6258",
    accent="#a35b2f",
    accent_soft="#ead3bf",
    border="#dbcbbc",
    success="#2f6f4f",
    danger="#9b3d2f",
)

DARK_TOKENS = ThemeTokens(
    canvas="#101318",
    surface="#171c22",
    surface_alt="#202731",
    ink="#f3eee7",
    muted="#b8aa9c",
    accent="#d18a57",
    accent_soft="#5a3b29",
    border="#2e3946",
    success="#5db187",
    danger="#dc7a6b",
)


def normalize_theme_mode(theme_mode: str | None) -> Literal["light", "dark"]:
    if theme_mode == "dark":
        return "dark"
    return "light"


def theme_tokens(theme_mode: str | None) -> ThemeTokens:
    return DARK_TOKENS if normalize_theme_mode(theme_mode) == "dark" else LIGHT_TOKENS


def build_theme_css(
    tokens: ThemeTokens | None = None,
    theme_mode: str | None = "light",
) -> str:
    normalized_mode = normalize_theme_mode(theme_mode)
    resolved = tokens or theme_tokens(normalized_mode)
    overlay_alpha = "0.16" if normalized_mode == "dark" else "0.08"
    gradient_end = "#161b22" if normalized_mode == "dark" else "#f8f3ec"
    sidebar_bg = "rgba(23, 28, 34, 0.92)" if normalized_mode == "dark" else "rgba(255, 250, 243, 0.86)"
    header_bg = "rgba(16, 19, 24, 0.82)" if normalized_mode == "dark" else "rgba(245, 239, 230, 0.78)"
    shell_bg = "rgba(23, 28, 34, 0.84)" if normalized_mode == "dark" else "rgba(255, 250, 243, 0.72)"
    shadow = "rgba(0, 0, 0, 0.32)" if normalized_mode == "dark" else "rgba(32, 26, 23, 0.06)"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@400;500;600;700&display=swap');
:root {{
  --zp-canvas: {resolved.canvas};
  --zp-surface: {resolved.surface};
  --zp-surface-alt: {resolved.surface_alt};
  --zp-ink: {resolved.ink};
  --zp-muted: {resolved.muted};
  --zp-accent: {resolved.accent};
  --zp-accent-soft: {resolved.accent_soft};
  --zp-border: {resolved.border};
  --zp-success: {resolved.success};
  --zp-danger: {resolved.danger};
}}
html, body, [data-testid="stAppViewContainer"] {{
  font-family: "Manrope", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(163, 91, 47, {overlay_alpha}), transparent 32%),
    linear-gradient(180deg, var(--zp-canvas) 0%, {gradient_end} 100%);
  color: var(--zp-ink);
}}
[data-testid="stAppViewContainer"] > .main {{
  background: transparent;
}}
[data-testid="stSidebar"] {{
  background: {sidebar_bg};
  border-right: 1px solid var(--zp-border);
}}
[data-testid="stHeader"] {{
  background: {header_bg};
}}
h1, h2, h3, h4, h5, h6 {{
  color: var(--zp-ink);
  letter-spacing: -0.02em;
}}
p, label, [data-testid="stMarkdownContainer"] {{
  color: var(--zp-ink);
}}
code, pre, textarea {{
  font-family: "IBM Plex Mono", monospace;
}}
.zp-page-shell {{
  background: {shell_bg};
  border: 1px solid var(--zp-border);
  border-radius: 24px;
  padding: 1.25rem 1.25rem 0.75rem;
  box-shadow: 0 24px 60px {shadow};
  backdrop-filter: blur(10px);
}}
.zp-page-shell__eyebrow {{
  color: var(--zp-muted);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  margin: 0 0 0.35rem;
  text-transform: uppercase;
}}
.zp-page-shell__title {{
  margin: 0;
}}
.zp-page-shell__summary {{
  color: var(--zp-muted);
  margin: 0.35rem 0 1rem;
  max-width: 48rem;
}}
div[data-testid="stRadio"] label {{
  font-weight: 600;
}}
</style>
""".strip()


def apply_theme(theme_mode: str | None = "light") -> None:
    import streamlit as st

    st.markdown(build_theme_css(theme_mode=theme_mode), unsafe_allow_html=True)
