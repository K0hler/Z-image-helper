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
    input_bg = "rgba(27, 34, 42, 0.96)" if normalized_mode == "dark" else "rgba(255, 250, 243, 0.96)"
    input_bg_hover = "rgba(34, 42, 52, 0.98)" if normalized_mode == "dark" else "rgba(250, 242, 232, 0.98)"
    input_bg_active = "rgba(39, 49, 61, 1)" if normalized_mode == "dark" else "rgba(255, 247, 238, 1)"
    code_bg = "rgba(20, 25, 31, 0.94)" if normalized_mode == "dark" else "rgba(246, 237, 225, 0.92)"
    button_text = "#f8f3ec" if normalized_mode == "dark" else "#201a17"
    toggle_glow = "rgba(209, 138, 87, 0.32)" if normalized_mode == "dark" else "rgba(163, 91, 47, 0.18)"
    toggle_thumb = "#f8f3ec" if normalized_mode == "dark" else "#fffaf3"
    toggle_translate = "1.1rem" if normalized_mode == "dark" else "0"
    toggle_icon = '"☾"' if normalized_mode == "dark" else '"☀"'
    panel_bg = "rgba(20, 26, 33, 0.92)" if normalized_mode == "dark" else "rgba(255, 250, 243, 0.9)"
    panel_bg_alt = "rgba(25, 31, 39, 0.96)" if normalized_mode == "dark" else "rgba(250, 243, 234, 0.95)"
    panel_bg_editor = "rgba(18, 24, 31, 0.96)" if normalized_mode == "dark" else "rgba(255, 251, 245, 0.98)"
    panel_bg_output = "rgba(23, 29, 36, 0.98)" if normalized_mode == "dark" else "rgba(252, 246, 238, 0.98)"
    panel_shadow = "rgba(3, 6, 10, 0.42)" if normalized_mode == "dark" else "rgba(32, 26, 23, 0.08)"
    border_soft = "rgba(98, 118, 138, 0.42)" if normalized_mode == "dark" else "rgba(171, 142, 118, 0.22)"
    panel_border = "rgba(112, 134, 156, 0.46)" if normalized_mode == "dark" else "rgba(167, 139, 114, 0.26)"
    panel_border_strong = "rgba(140, 168, 196, 0.52)" if normalized_mode == "dark" else "rgba(173, 135, 102, 0.3)"
    input_border = "rgba(95, 111, 128, 0.42)" if normalized_mode == "dark" else "rgba(188, 163, 140, 0.38)"
    input_border_hover = "rgba(130, 149, 170, 0.52)" if normalized_mode == "dark" else "rgba(177, 144, 116, 0.44)"
    input_border_focus = "rgba(209, 138, 87, 0.75)" if normalized_mode == "dark" else "rgba(163, 91, 47, 0.58)"
    muted_chip_bg = "rgba(45, 55, 66, 0.92)" if normalized_mode == "dark" else "rgba(239, 229, 216, 0.95)"
    muted_chip_text = "#d9cfc4" if normalized_mode == "dark" else "#5d5045"
    accent_chip_bg = "rgba(98, 62, 39, 0.92)" if normalized_mode == "dark" else "rgba(234, 211, 191, 0.95)"
    accent_chip_text = "#ffd9bf" if normalized_mode == "dark" else "#7b4320"

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
[data-testid="stAppViewBlockContainer"] {{
  padding-top: 2rem;
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
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stForm"] {{
  border-radius: 24px;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
  border-color: transparent !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] > div {{
  background: transparent;
}}
[data-testid="stForm"] {{
  background: {panel_bg_alt};
  border: 1px solid {panel_border};
  box-shadow: 0 14px 30px {panel_shadow};
}}
.st-key-workbench_header_panel,
.st-key-workbench_editor_panel,
.st-key-workbench_output_panel {{
  border-radius: 24px;
  border: 1px solid {panel_border};
  box-shadow: 0 18px 38px {panel_shadow};
}}
.st-key-workbench_header_panel {{
  background: {panel_bg};
}}
.st-key-workbench_editor_panel {{
  background: {panel_bg_editor};
  border-color: {panel_border_strong};
}}
.st-key-workbench_output_panel {{
  background: {panel_bg_output};
  border-color: {panel_border_strong};
}}
[data-testid="stHorizontalBlock"] .st-key-workbench_editor_panel,
[data-testid="stHorizontalBlock"] .st-key-workbench_output_panel {{
  position: relative;
}}
[data-testid="stHorizontalBlock"] .st-key-workbench_editor_panel::after,
[data-testid="stHorizontalBlock"] .st-key-workbench_output_panel::after {{
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 24px;
  pointer-events: none;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}}
[data-testid="stTextInputRootElement"],
[data-testid="stNumberInputContainer"] {{
  border: 1px solid {input_border} !important;
  border-radius: 18px !important;
  background: {input_bg} !important;
  background-color: {input_bg} !important;
  box-shadow: none !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] {{
  background: {input_bg} !important;
  background-color: {input_bg} !important;
  background-image: none !important;
  color: var(--zp-ink) !important;
  border: 1px solid {input_border} !important;
  box-shadow: none !important;
  overflow: hidden !important;
}}
[data-testid="stTextInputRootElement"] [data-baseweb="base-input"],
[data-testid="stNumberInput"] [data-baseweb="base-input"],
[data-testid="stNumberInputContainer"] > div {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  color: var(--zp-ink) !important;
  border: none !important;
  box-shadow: none !important;
  overflow: hidden !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"] > div,
[data-testid="stTextInputRootElement"] [data-baseweb="base-input"] > div,
[data-testid="stNumberInput"] [data-baseweb="base-input"] > div {{
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stNumberInput"] [data-baseweb="base-input"],
[data-testid="stTextInputRootElement"] [data-baseweb="base-input"] {{
  border-radius: 18px !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
  overflow: hidden !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div > div {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: 0 !important;
  box-shadow: none !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSelectbox"] [data-baseweb="select"] *::before,
[data-testid="stSelectbox"] [data-baseweb="select"] *::after {{
  box-shadow: none !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] [aria-hidden="true"] {{
  border: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"]:hover,
[data-testid="stTextInputRootElement"]:hover,
[data-testid="stNumberInputContainer"]:hover,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
[data-baseweb="textarea"]:hover {{
  background: {input_bg_hover} !important;
  background-color: {input_bg_hover} !important;
  background-image: none !important;
  border-color: {input_border_hover} !important;
}}
[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-baseweb="textarea"]:focus-within {{
  background: {input_bg_active} !important;
  background-color: {input_bg_active} !important;
  background-image: none !important;
  border-color: {input_border_focus} !important;
  box-shadow: none !important;
}}
[data-testid="stTextArea"] textarea,
[data-testid="stTextInputRootElement"] input,
[data-testid="stNumberInput"] input {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  color: var(--zp-ink) !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  caret-color: var(--zp-ink) !important;
}}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextArea"] textarea:focus-visible,
[data-testid="stTextInputRootElement"] input:focus,
[data-testid="stTextInputRootElement"] input:focus-visible,
[data-testid="stNumberInput"] input:focus,
[data-testid="stNumberInput"] input:focus-visible {{
  background: transparent !important;
  background-color: transparent !important;
  outline: none !important;
  box-shadow: none !important;
}}
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInputRootElement"] input::placeholder {{
  color: var(--zp-muted) !important;
}}
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] span {{
  color: var(--zp-ink) !important;
}}
[data-testid="stCheckbox"] [role="checkbox"] {{
  border-color: var(--zp-border) !important;
  background: {input_bg} !important;
}}
[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] {{
  background: var(--zp-accent) !important;
  border-color: var(--zp-accent) !important;
}}
[data-baseweb="popover"] {{
  border-radius: 18px !important;
  overflow: clip !important;
  border: 1px solid {input_border} !important;
  background: {input_bg} !important;
  background-color: {input_bg} !important;
  box-shadow: 0 20px 40px {panel_shadow} !important;
  padding: 0 !important;
  outline: none !important;
}}
[data-baseweb="popover"] > div {{
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 0 !important;
  border-radius: 0 !important;
  overflow: visible !important;
}}
[data-baseweb="popover"] > div > div {{
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 0 !important;
  border-radius: 0 !important;
  overflow: visible !important;
}}
[data-baseweb="popover"] ul {{
  background: transparent !important;
  background-color: transparent !important;
  color: var(--zp-ink) !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 0.35rem 0 !important;
  border-radius: 0 !important;
}}
[data-baseweb="popover"] ::-webkit-scrollbar {{
  width: 0 !important;
  height: 0 !important;
  display: none !important;
  background: transparent;
}}
[data-baseweb="popover"] li[role="option"],
[data-baseweb="popover"] [role="option"] {{
  background: transparent !important;
  background-color: transparent !important;
  color: var(--zp-ink) !important;
  border: 0 !important;
  box-shadow: none !important;
}}
[data-baseweb="popover"] li[role="option"]:hover,
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] li[role="option"][aria-selected="true"],
[data-baseweb="popover"] [role="option"][aria-selected="true"] {{
  background: {input_bg_hover} !important;
  background-color: {input_bg_hover} !important;
  color: var(--zp-ink) !important;
}}
[data-baseweb="popover"] [role="option"] * {{
  color: inherit !important;
}}
[data-baseweb="popover"] * {{
  box-shadow: none !important;
}}
[data-testid="stRadio"] > div {{
  gap: 0.5rem;
}}
div[role="radiogroup"] > label {{
  background: {input_bg};
  border: 1px solid var(--zp-border);
  border-radius: 999px;
  padding: 0.3rem 0.85rem;
  transition: background 180ms ease, border-color 180ms ease, transform 180ms ease;
}}
div[role="radiogroup"] > label:hover {{
  background: {input_bg_hover};
  border-color: var(--zp-accent);
  transform: translateY(-1px);
}}
[data-testid="stButton"] button {{
  border-radius: 999px;
  border: 1px solid {panel_border};
  background: {input_bg};
  color: var(--zp-ink);
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
}}
[data-testid="stButton"] button:hover {{
  border-color: var(--zp-accent);
  background: {input_bg_hover};
  transform: translateY(-1px);
  box-shadow: 0 12px 28px {shadow};
}}
[data-testid="stButton"] button[kind="primary"] {{
  background: linear-gradient(135deg, var(--zp-accent) 0%, #c4723c 100%);
  color: {button_text};
  border-color: transparent;
}}
[data-testid="stButton"] button[kind="primary"]:hover {{
  background: linear-gradient(135deg, #b76734 0%, #d28a58 100%);
}}
[data-testid="stFormSubmitButton"] button {{
  border-radius: 999px !important;
  border: 1px solid {panel_border} !important;
  background: {input_bg} !important;
  color: var(--zp-ink) !important;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
}}
[data-testid="stFormSubmitButton"] button:hover {{
  border-color: var(--zp-accent) !important;
  background: {input_bg_hover} !important;
  transform: translateY(-1px);
  box-shadow: 0 12px 28px {shadow};
}}
[data-testid="stNumberInputStepDown"],
[data-testid="stNumberInputStepUp"] {{
  background: {input_bg} !important;
  background-color: {input_bg} !important;
  color: var(--zp-ink) !important;
  border: none !important;
  border-left: 1px solid {input_border} !important;
}}
[data-testid="stNumberInputStepDown"]:hover,
[data-testid="stNumberInputStepUp"]:hover {{
  background: {input_bg_hover} !important;
  background-color: {input_bg_hover} !important;
}}
[data-testid="stTextInputRootElement"] button {{
  background: transparent !important;
  background-color: transparent !important;
  color: var(--zp-ink) !important;
  border: none !important;
}}
[data-testid="stTextInputRootElement"] button svg {{
  fill: var(--zp-ink) !important;
}}
[data-testid="stTabs"] [role="tablist"] {{
  gap: 0.5rem;
}}
[data-testid="stTabs"] [role="tab"] {{
  border-radius: 999px;
  border: 1px solid var(--zp-border);
  background: {input_bg};
}}
[data-testid="stTabs"] [aria-selected="true"] {{
  border-color: var(--zp-accent);
  color: var(--zp-accent);
}}
[data-testid="stPopover"] > div > button {{
  background: {input_bg};
}}
[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] {{
  background: {code_bg} !important;
}}
.zp-page-shell {{
  background: {shell_bg};
  border: 1px solid {border_soft};
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
.zp-toolbar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}}
.zp-toolbar__nav {{
  flex: 1 1 auto;
}}
.zp-toolbar__theme {{
  flex: 0 0 auto;
}}
.zp-status-chip {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  min-height: 2rem;
  margin: 0.5rem 0 0.75rem;
  padding: 0.32rem 0.72rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}}
.zp-status-chip__icon {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  opacity: 0.9;
}}
.zp-status-chip--muted {{
  background: {muted_chip_bg};
  color: {muted_chip_text};
  border-color: rgba(255, 255, 255, 0.05);
}}
.zp-status-chip--accent {{
  background: {accent_chip_bg};
  color: {accent_chip_text};
  border-color: rgba(209, 138, 87, 0.22);
}}
.zp-meta-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.9rem;
}}
.zp-meta-card {{
  background: {panel_bg_alt};
  border: 1px solid {panel_border};
  border-radius: 18px;
  padding: 0.85rem 0.95rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}}
.zp-meta-card strong {{
  display: block;
  font-size: 1.1rem;
  margin-bottom: 0.2rem;
}}
.zp-meta-card span,
.zp-empty {{
  color: var(--zp-muted);
}}
.st-key-short_idea_section {{
  border-left: 3px solid var(--zp-accent);
  padding-left: 0.85rem;
  border-radius: 2px;
  margin-bottom: 0.15rem;
}}
.zp-idea-label {{
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--zp-accent);
  margin: 0 0 0.15rem;
}}
.st-key-workbench_editor_panel [data-testid="stCheckbox"] {{
  margin-top: 0.5rem;
  margin-bottom: -0.2rem;
  padding: 0;
}}
.st-key-workbench_editor_panel [data-testid="stCheckbox"] label {{
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  color: var(--zp-muted) !important;
  gap: 0.45rem;
}}
.st-key-workbench_editor_panel [data-testid="stTextArea"] {{
  margin-bottom: 0 !important;
}}
.st-key-workbench_editor_panel hr {{
  margin: 0.55rem 0 0.35rem;
  opacity: 0.45;
}}
div[data-testid="stRadio"] label {{
  font-weight: 600;
}}
.st-key-theme_toggle button {{
  position: relative;
  min-width: 2.5rem !important;
  width: 2.5rem !important;
  height: 2.5rem !important;
  padding: 0 !important;
  border-radius: 999px !important;
  background: {input_bg} !important;
  border: 1px solid var(--zp-border) !important;
  box-shadow: 0 4px 14px {toggle_glow};
  transition: background 200ms ease, border-color 200ms ease, box-shadow 200ms ease, transform 180ms ease;
}}
.st-key-theme_toggle button::before {{
  display: none;
}}
.st-key-theme_toggle button > div,
.st-key-theme_toggle button p {{
  opacity: 0;
}}
.st-key-theme_toggle button::after {{
  content: {toggle_icon};
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--zp-ink);
  font-size: 1.15rem;
}}
.st-key-theme_toggle button:hover {{
  border-color: var(--zp-accent) !important;
  background: {input_bg_hover} !important;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px {toggle_glow};
}}
.st-key-editor_gen_row [data-testid="stHorizontalBlock"],
.st-key-editor_ctrl_row [data-testid="stHorizontalBlock"],
.st-key-output_action_row [data-testid="stHorizontalBlock"] {{
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-start;
}}
.st-key-editor_gen_row .stColumn,
.st-key-editor_ctrl_row .stColumn,
.st-key-output_action_row .stColumn {{
  flex: 0 0 auto !important;
  width: auto !important;
  min-width: 0 !important;
}}
.st-key-editor_gen_row [data-testid="stButton"] button,
.st-key-editor_ctrl_row [data-testid="stButton"] button,
.st-key-output_action_row [data-testid="stButton"] button {{
  white-space: nowrap;
}}
.st-key-generate button {{
  background: linear-gradient(135deg, #1d6b40 0%, #268050 100%) !important;
  color: #e4f7ed !important;
  border-color: rgba(38, 128, 80, 0.4) !important;
}}
.st-key-generate button:hover {{
  background: linear-gradient(135deg, #268050 0%, #309a61 100%) !important;
  border-color: rgba(48, 154, 97, 0.5) !important;
  transform: translateY(-1px);
}}
.st-key-copy_prompt button {{
  background: linear-gradient(135deg, #7a5c0e 0%, #9e7918 100%) !important;
  color: #fef8e2 !important;
  border-color: rgba(158, 121, 24, 0.4) !important;
}}
.st-key-copy_prompt button:hover {{
  background: linear-gradient(135deg, #9e7918 0%, #be9422 100%) !important;
  border-color: rgba(190, 148, 34, 0.5) !important;
  transform: translateY(-1px);
}}
[data-testid="stToast"] {{
  background: {panel_bg} !important;
  background-color: {panel_bg} !important;
  border: 1px solid {panel_border} !important;
  border-radius: 18px !important;
  box-shadow: 0 16px 36px {panel_shadow} !important;
}}
[data-testid="stToast"] p,
[data-testid="stToast"] span,
[data-testid="stToast"] div,
[data-testid="stToast"] [data-testid="stMarkdownContainer"] {{
  color: var(--zp-ink) !important;
}}
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p {{
  color: var(--zp-ink) !important;
}}
@media (max-width: 900px) {{
  .zp-meta-grid {{
    grid-template-columns: 1fr;
  }}
}}
</style>
""".strip()


def apply_theme(theme_mode: str | None = "light") -> None:
    import streamlit as st

    st.markdown(build_theme_css(theme_mode=theme_mode), unsafe_allow_html=True)
