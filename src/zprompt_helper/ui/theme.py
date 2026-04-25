from dataclasses import dataclass


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


def build_theme_css(tokens: ThemeTokens = ThemeTokens()) -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root {{
      --zp-canvas: {tokens.canvas};
      --zp-surface: {tokens.surface};
      --zp-surface-alt: {tokens.surface_alt};
      --zp-ink: {tokens.ink};
      --zp-muted: {tokens.muted};
      --zp-accent: {tokens.accent};
      --zp-accent-soft: {tokens.accent_soft};
      --zp-border: {tokens.border};
      --zp-success: {tokens.success};
      --zp-danger: {tokens.danger};
      --zp-radius-lg: 22px;
      --zp-radius-md: 16px;
    }}
    html, body, [data-testid="stAppViewContainer"] {{
      font-family: "Manrope", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(234, 211, 191, 0.45), transparent 28%),
        linear-gradient(180deg, #fbf6ef 0%, var(--zp-canvas) 32%, #efe5d8 100%);
      color: var(--zp-ink);
    }}
    [data-testid="stAppViewContainer"] > .main {{
      background: transparent;
    }}
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 {{
      letter-spacing: -0.03em;
      color: var(--zp-ink);
    }}
    [data-testid="stTextArea"] textarea,
    code, pre {{
      font-family: "IBM Plex Mono", monospace;
    }}
    .zp-shell {{
      padding: 0.2rem 0 1.2rem;
    }}
    .zp-shell__eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.35rem 0.7rem;
      border: 1px solid var(--zp-border);
      border-radius: 999px;
      background: rgba(255, 250, 243, 0.88);
      color: var(--zp-muted);
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .zp-shell__title {{
      margin: 0.85rem 0 0.35rem;
      font-size: clamp(2.15rem, 5vw, 3.45rem);
      line-height: 0.96;
      font-weight: 800;
    }}
    .zp-shell__lede {{
      max-width: 52rem;
      color: var(--zp-muted);
      font-size: 1rem;
      line-height: 1.6;
    }}
    .zp-meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 0.75rem;
      margin-top: 1rem;
    }}
    .zp-meta-card {{
      padding: 0.85rem 1rem;
      border: 1px solid var(--zp-border);
      border-radius: var(--zp-radius-md);
      background: rgba(255, 250, 243, 0.82);
    }}
    .zp-meta-card strong {{
      display: block;
      font-size: 1.05rem;
    }}
    .zp-meta-card span {{
      color: var(--zp-muted);
      font-size: 0.88rem;
    }}
    .zp-empty {{
      padding: 1rem;
      border: 1px dashed var(--zp-border);
      border-radius: var(--zp-radius-md);
      background: rgba(255, 250, 243, 0.6);
      color: var(--zp-muted);
    }}
    </style>
    """


def apply_theme() -> None:
    import streamlit as st

    st.markdown(build_theme_css(), unsafe_allow_html=True)
