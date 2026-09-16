from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ThemeTokens:
    canvas: str = "#f5f5f4"
    surface: str = "#ffffff"
    surface_alt: str = "#f0f0ef"
    ink: str = "#232326"
    muted: str = "#6f7075"
    accent: str = "#52525b"
    accent_soft: str = "#e7e7e9"
    border: str = "#dedede"
    success: str = "#5f6670"
    danger: str = "#a34e43"


LIGHT_TOKENS = ThemeTokens()

DARK_TOKENS = ThemeTokens(
    canvas="#111214",
    surface="#191b1f",
    surface_alt="#23262b",
    ink="#f2f2f0",
    muted="#a5a7ad",
    accent="#b0b2b8",
    accent_soft="#2b2e34",
    border="#383b42",
    success="#a5a7ad",
    danger="#df8175",
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
    sidebar = "#151619" if normalized_mode == "dark" else "#efefee"
    input_bg = "#202226" if normalized_mode == "dark" else "#fbfbfa"
    hover_bg = "#272a2f" if normalized_mode == "dark" else "#f0f0ef"
    code_bg = "#15171a" if normalized_mode == "dark" else "#f3f3f2"
    primary_bg = "#5f636d" if normalized_mode == "dark" else resolved.accent
    primary_text = "#ffffff"

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
  background: var(--zp-canvas);
  color: var(--zp-ink);
}}

code, pre, textarea {{
  font-family: "IBM Plex Mono", monospace;
}}

[data-testid="stHeader"] {{
  background: transparent;
}}

[data-testid="stAppViewBlockContainer"] {{
  max-width: 1500px;
  padding-top: 1.75rem;
  padding-bottom: 3rem;
}}

h1, h2, h3, h4, h5, h6,
p, label, [data-testid="stMarkdownContainer"] {{
  color: var(--zp-ink);
}}

h1 {{
  font-size: clamp(2rem, 3vw, 2.75rem) !important;
  letter-spacing: -0.04em !important;
  margin-bottom: 0.15rem !important;
}}

h2, h3 {{
  letter-spacing: -0.025em !important;
}}

[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {{
  color: var(--zp-muted) !important;
}}

[data-testid="stSidebar"] {{
  background: {sidebar};
  border-right: 1px solid var(--zp-border);
}}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
  padding: 1.2rem 0.85rem;
}}

[data-testid="stSidebar"] h2 {{
  color: var(--zp-accent);
  font-size: 1.35rem !important;
  letter-spacing: 0.04em !important;
  margin-bottom: 0 !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {{
  gap: 0.3rem;
}}

[data-testid="stSidebar"] div[role="radiogroup"] > label {{
  min-height: 2.8rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid transparent;
  border-radius: 10px;
  transition: background 140ms ease, border-color 140ms ease;
}}

[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
  background: {hover_bg};
}}

[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
  background: var(--zp-accent-soft);
  border-color: var(--zp-border);
}}

[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {{
  color: var(--zp-accent) !important;
  font-weight: 700 !important;
}}

.st-key-theme_toggle {{
  margin-top: 1rem;
}}

.st-key-theme_toggle button {{
  width: 100%;
}}

.st-key-workbench_composer_panel,
.st-key-workbench_editor_panel,
.st-key-workbench_output_panel {{
  background: var(--zp-surface);
  border: 1px solid var(--zp-border) !important;
  border-radius: 16px !important;
  box-shadow: none !important;
}}

.st-key-workbench_composer_panel,
.st-key-workbench_editor_panel {{
  margin-bottom: 1rem;
}}

.st-key-workbench_composer_panel [data-testid="stTextArea"] textarea {{
  min-height: 7.25rem !important;
}}

.st-key-composer_secondary_actions,
.st-key-output_action_row {{
  align-items: center;
  gap: 0.55rem;
}}

.st-key-generate button {{
  min-height: 3rem;
  background: {primary_bg} !important;
  border-color: {primary_bg} !important;
  color: {primary_text} !important;
  font-weight: 700 !important;
}}

.st-key-generate button p,
.st-key-generate button span,
.st-key-generate button svg {{
  color: {primary_text} !important;
  fill: {primary_text} !important;
}}

.st-key-generate button:hover {{
  filter: brightness(0.94);
}}

[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stPopover"] > div > button {{
  border-radius: 10px !important;
  box-shadow: none !important;
  transition: background 140ms ease, border-color 140ms ease;
}}

[data-testid="stButton"] button:not([kind="primary"]),
[data-testid="stFormSubmitButton"] button,
[data-testid="stPopover"] > div > button {{
  background: var(--zp-surface) !important;
  border-color: var(--zp-border) !important;
  color: var(--zp-ink) !important;
}}

[data-testid="stButton"] button:not([kind="primary"]):hover,
[data-testid="stFormSubmitButton"] button:hover,
[data-testid="stPopover"] > div > button:hover {{
  background: {hover_bg} !important;
  border-color: var(--zp-accent) !important;
}}

[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextArea"] [data-baseweb="base-input"],
[data-testid="stTextInputRootElement"],
[data-testid="stTextInputRootElement"] [data-baseweb="base-input"],
[data-testid="stNumberInputContainer"],
[data-testid="stNumberInputContainer"] [data-baseweb="base-input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
  background: {input_bg} !important;
  border-color: var(--zp-border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}

[data-testid="stTextArea"] textarea,
[data-testid="stTextInputRootElement"] input,
[data-testid="stNumberInput"] input {{
  color: var(--zp-ink) !important;
  caret-color: var(--zp-ink) !important;
  -webkit-text-fill-color: var(--zp-ink) !important;
}}

[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div * {{
  color: var(--zp-ink) !important;
  -webkit-text-fill-color: var(--zp-ink) !important;
}}

[data-testid="stSelectbox"] [data-baseweb="select"] svg {{
  fill: var(--zp-ink) !important;
}}

[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInputRootElement"] input::placeholder {{
  color: var(--zp-muted) !important;
}}

[data-testid="stExpander"] {{
  background: var(--zp-surface);
  border: 1px solid var(--zp-border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  overflow: hidden;
}}

[data-testid="stExpander"] summary {{
  min-height: 3rem;
  background: var(--zp-surface) !important;
  color: var(--zp-ink) !important;
}}

[data-testid="stExpander"] details[open] > summary {{
  background: var(--zp-surface-alt) !important;
}}

[data-testid="stExpander"] summary *,
[data-testid="stExpander"] summary p {{
  color: var(--zp-ink) !important;
  fill: var(--zp-ink) !important;
}}

[data-testid="stExpander"] summary:hover {{
  background: {hover_bg};
}}

[data-testid="stToggle"] p,
[data-testid="stCheckbox"] p {{
  color: var(--zp-muted) !important;
  font-size: 0.85rem !important;
}}

[data-testid="stTabs"] [role="tablist"] {{
  gap: 1.25rem;
}}

[data-testid="stTabs"] [role="tab"] {{
  padding-left: 0;
  padding-right: 0;
}}

[data-testid="stTabs"] [aria-selected="true"] {{
  color: var(--zp-accent) !important;
}}

[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] {{
  background: {code_bg} !important;
  border-color: var(--zp-border) !important;
}}

[data-baseweb="popover"] {{
  background: var(--zp-surface) !important;
  border: 1px solid var(--zp-border) !important;
  border-radius: 12px !important;
  box-shadow: 0 12px 30px rgba(20, 28, 23, 0.12) !important;
}}

[data-baseweb="popover"] > div,
[data-baseweb="popover"] ul {{
  background: var(--zp-surface) !important;
  color: var(--zp-ink) !important;
}}

[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {{
  color: var(--zp-ink) !important;
  -webkit-text-fill-color: var(--zp-ink) !important;
}}

[data-baseweb="popover"] [role="option"] > div {{
  background: transparent !important;
}}

[data-baseweb="popover"] [role="option"]:hover > div {{
  background: {hover_bg} !important;
}}

[data-baseweb="popover"] [role="option"][aria-selected="true"] > div {{
  background: var(--zp-accent-soft) !important;
}}

[data-baseweb="popover"] [class*="st-key-use-idea-history-"] button {{
  width: 100% !important;
  min-height: 2.4rem !important;
  justify-content: flex-start !important;
  border: 0 !important;
  background: transparent !important;
  text-align: left !important;
  white-space: normal !important;
}}

[data-baseweb="popover"] [class*="st-key-use-idea-history-"] button:hover {{
  background: {hover_bg} !important;
}}

[data-testid="stToast"] {{
  background: var(--zp-surface) !important;
  border: 1px solid var(--zp-border) !important;
  border-radius: 12px !important;
  box-shadow: 0 12px 30px rgba(20, 28, 23, 0.12) !important;
}}

@media (min-width: 901px) {{
  .st-key-workbench_output_panel {{
    position: sticky;
    top: 1rem;
  }}
}}

@media (max-width: 900px) {{
  [data-testid="stAppViewBlockContainer"] {{
    padding-top: 1rem;
  }}

  .st-key-workbench_output_panel {{
    position: static;
  }}
}}
</style>
""".strip()


def apply_theme(theme_mode: str | None = "light") -> None:
    import streamlit as st

    st.markdown(build_theme_css(theme_mode=theme_mode), unsafe_allow_html=True)
