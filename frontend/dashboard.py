"""
dashboard.py — Streamlit frontend for *Sentinel — Early Mental-Health Signals*.

Sentinel surfaces early mental-health risk through daily check-ins, NLP
analysis of journal text, anomaly detection, and a non-negotiable safety
screen for crisis language. This file is the single-page frontend that
orchestrates a branded landing experience plus the live dashboard.

Pages (state-routed via ``st.session_state["page"]``):
    - Home       — hero, problem statement, solution pipeline, value props
    - Dashboard  — daily check-in form (sidebar) + assessment / trends / history
    - About      — mission, vision, design principles
    - Solution   — deeper explainer of the ML pipeline + weights + safety screen
    - Resources  — crisis hotlines, "when to seek help" guidance, FAQ

Design system: modern dark theme (deep navy / indigo / cyan), Inter +
Plus Jakarta Sans, 8-pt spacing scale. All custom styling is consolidated
in the ``CUSTOM_CSS`` block near the top of the file for maintainability.
"""

import datetime
import os

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ===========================================================================
# CONFIGURATION
# ===========================================================================
# API base URL is configurable via the BHRM_API_BASE_URL env var so the
# frontend can point at remote / containerised backends without code edits.
API_BASE_URL = os.environ.get("BHRM_API_BASE_URL", "http://localhost:8000")

# Pages reachable via the navbar. Order is preserved in the rendered nav.
PAGES = ["Home", "Dashboard", "About", "Solution", "Resources"]
DEFAULT_PAGE = "Home"

st.set_page_config(
    page_title="Sentinel — Early Mental-Health Signals",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialise routing state up-front so the navbar can read it on first render.
if "page" not in st.session_state:
    st.session_state["page"] = DEFAULT_PAGE


def _go_to(page: str) -> None:
    """Route helper used by nav buttons + CTA buttons throughout the app."""
    st.session_state["page"] = page


# ===========================================================================
# DESIGN SYSTEM — single source of truth for colours, gradients, etc.
# ===========================================================================
# These constants are referenced inline in the Plotly themes and a couple
# of HTML snippets. The bulk of the styling lives in CUSTOM_CSS below.
COLOR_BG = "#0a0e1a"
COLOR_SURFACE = "#111827"
COLOR_INDIGO = "#6366f1"
COLOR_CYAN = "#22d3ee"
COLOR_TEAL = "#14b8a6"
COLOR_AMBER = "#f59e0b"
COLOR_ROSE = "#f43f5e"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_MUTED = "#94a3b8"


# ---------------------------------------------------------------------------
# Inline brand mark (SVG). Rendered in the navbar + hero. Kept inline so
# the file is self-contained — no /static asset pipeline needed.
# ---------------------------------------------------------------------------
SENTINEL_LOGO_SVG = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-label="Sentinel logo">
  <defs>
    <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#22d3ee"/>
      <stop offset="100%" stop-color="#6366f1"/>
    </linearGradient>
  </defs>
  <path d="M32 4 L56 14 L56 30 C56 46 44 56 32 60 C20 56 8 46 8 30 L8 14 Z"
        fill="url(#sg)" opacity="0.18"
        stroke="url(#sg)" stroke-width="2.2" stroke-linejoin="round"/>
  <path d="M14 34 L22 34 L26 24 L32 44 L38 28 L42 34 L50 34"
        fill="none" stroke="url(#sg)" stroke-width="3.2"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""".strip()


# ===========================================================================
# CUSTOM CSS — design tokens, typography, navbar, hero, cards, footer.
# ===========================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {
    --bg-0: #070a14;
    --bg-1: #0a0e1a;
    --bg-2: #111827;
    --surface: rgba(255,255,255,0.03);
    --surface-2: rgba(255,255,255,0.05);
    --border: rgba(255,255,255,0.08);
    --border-strong: rgba(255,255,255,0.14);
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --indigo: #6366f1;
    --indigo-soft: rgba(99,102,241,0.18);
    --cyan: #22d3ee;
    --cyan-soft: rgba(34,211,238,0.16);
    --teal: #14b8a6;
    --rose: #f43f5e;
    --amber: #f59e0b;
    --emerald: #10b981;
    --grad-brand: linear-gradient(135deg, #22d3ee 0%, #6366f1 100%);
    --shadow-card: 0 12px 40px rgba(0,0,0,0.35);
}

/* Global background — layered radial glows on a deep navy base */
.stApp {
    background:
        radial-gradient(1200px 600px at 10% -10%, rgba(99,102,241,0.18), transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(34,211,238,0.14), transparent 60%),
        linear-gradient(180deg, #070a14 0%, #0a0e1a 50%, #111827 100%);
    color: var(--text);
}

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: var(--text);
}
h1, h2, h3, h4 {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    color: var(--text);
    letter-spacing: -0.01em;
}

/* Hide default Streamlit chrome that fights the custom design */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* Tame the default block container so the navbar can sit flush */
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}

/* ===================================================================
   NAVBAR
   =================================================================== */
.sentinel-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 22px;
    margin: 0 0 24px 0;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
    border: 1px solid var(--border);
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.28);
}
.sentinel-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}
.sentinel-brand .logo {
    width: 38px; height: 38px;
    display: inline-flex; align-items: center; justify-content: center;
}
.sentinel-brand .logo svg { width: 100%; height: 100%; }
.sentinel-brand .wordmark {
    display: flex; flex-direction: column; line-height: 1.1;
}
.sentinel-brand .wordmark .name {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800; font-size: 1.15rem;
    background: var(--grad-brand);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.sentinel-brand .wordmark .tagline {
    font-size: 0.72rem; color: var(--text-muted);
    letter-spacing: 0.04em; text-transform: uppercase;
}

/* Streamlit renders our nav buttons inside the flex row. We re-style
   them to look like a horizontal link bar instead of bulky buttons. */
.sentinel-nav-row [data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    padding: 8px 14px !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    transition: all 0.18s ease;
}
.sentinel-nav-row [data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}
.sentinel-nav-row [data-testid="stButton"] > button:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px var(--cyan-soft) !important;
}
/* Active nav item — emitted via wrapping a button in .nav-active div  */
.sentinel-nav-row .nav-active [data-testid="stButton"] > button {
    background: var(--indigo-soft) !important;
    color: #c7d2fe !important;
    border-color: rgba(99,102,241,0.45) !important;
}

/* ===================================================================
   HERO
   =================================================================== */
.hero {
    padding: 56px 36px 60px 36px;
    border-radius: 24px;
    background:
        radial-gradient(700px 320px at 90% 10%, rgba(34,211,238,0.16), transparent 60%),
        radial-gradient(700px 320px at 0% 100%, rgba(99,102,241,0.18), transparent 60%),
        linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015));
    border: 1px solid var(--border);
    box-shadow: var(--shadow-card);
    margin-bottom: 32px;
}
.hero .eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 12px; border-radius: 999px;
    background: rgba(34,211,238,0.10);
    border: 1px solid rgba(34,211,238,0.28);
    color: #67e8f9; font-size: 0.78rem; letter-spacing: 0.06em;
    text-transform: uppercase; font-weight: 600;
    margin-bottom: 18px;
}
.hero h1 {
    font-size: clamp(2.1rem, 4.2vw, 3.4rem);
    line-height: 1.1; font-weight: 800;
    margin: 0 0 14px 0;
}
.hero h1 .accent {
    background: var(--grad-brand);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.hero p.lede {
    font-size: 1.08rem; color: var(--text-muted);
    max-width: 720px; line-height: 1.65; margin: 0 0 28px 0;
}
.hero-meta {
    display: flex; gap: 22px; flex-wrap: wrap; margin-top: 22px;
    color: var(--text-dim); font-size: 0.85rem;
}
.hero-meta span::before {
    content: "✓"; color: var(--cyan); margin-right: 6px; font-weight: 700;
}

/* ===================================================================
   SECTIONS / CARDS
   =================================================================== */
.section-eyebrow {
    color: var(--cyan); font-size: 0.78rem; letter-spacing: 0.16em;
    text-transform: uppercase; font-weight: 700; margin-bottom: 6px;
}
.section-title {
    font-size: clamp(1.6rem, 3vw, 2.2rem);
    font-weight: 800; margin: 0 0 10px 0;
}
.section-lede {
    color: var(--text-muted); font-size: 1.02rem; line-height: 1.65;
    max-width: 720px; margin-bottom: 28px;
}

.card {
    padding: 22px 22px 20px 22px;
    border-radius: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    transition: transform 0.18s ease, border-color 0.18s ease;
    height: 100%;
}
.card:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong);
}
.card .card-icon {
    width: 40px; height: 40px;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 10px; font-size: 1.2rem;
    background: var(--indigo-soft); color: #c7d2fe;
    margin-bottom: 12px;
}
.card h4 {
    margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 700;
}
.card p {
    margin: 0; color: var(--text-muted); font-size: 0.92rem;
    line-height: 1.55;
}

/* Stat cards — for the problem-statement section */
.stat-card {
    padding: 22px 20px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(99,102,241,0.10), rgba(34,211,238,0.04));
    border: 1px solid rgba(99,102,241,0.24);
    height: 100%;
}
.stat-card .stat-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.1rem; font-weight: 800; line-height: 1;
    background: var(--grad-brand);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 6px;
}
.stat-card .stat-label {
    color: var(--text); font-weight: 600; font-size: 0.95rem; margin-bottom: 4px;
}
.stat-card .stat-source {
    color: var(--text-dim); font-size: 0.78rem;
}

/* Pipeline (Our Solution) — connected step cards */
.pipeline {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}
.pipe-step {
    position: relative;
    padding: 20px;
    border-radius: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
}
.pipe-step .pipe-num {
    width: 30px; height: 30px; border-radius: 50%;
    background: var(--grad-brand); color: #0a0e1a;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.95rem; margin-bottom: 10px;
}
.pipe-step h4 { margin: 0 0 6px 0; font-size: 1rem; }
.pipe-step p { margin: 0; color: var(--text-muted); font-size: 0.88rem; line-height: 1.5; }

/* CTA strip */
.cta-strip {
    margin-top: 40px;
    padding: 32px 28px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(34,211,238,0.12));
    border: 1px solid rgba(99,102,241,0.36);
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
    gap: 18px;
}
.cta-strip h3 { margin: 0 0 6px 0; font-size: 1.4rem; font-weight: 800; }
.cta-strip p { margin: 0; color: var(--text-muted); font-size: 0.95rem; }

/* ===================================================================
   STREAMLIT WIDGETS — re-skinned
   =================================================================== */
/* Primary buttons (Submit Check-In, Demo, Hero CTAs) */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stButton"] > button.primary,
.stDownloadButton > button {
    background: var(--grad-brand) !important;
    color: #0a0e1a !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.32) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 32px rgba(99,102,241,0.42) !important;
}

/* Secondary buttons */
[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}

/* Sidebar (Dashboard check-in form) */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0e1a 0%, #070a14 100%);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: var(--surface);
    border-radius: 14px;
    border: 1px solid var(--border);
}

/* Metric cards (Streamlit native) */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
}
[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 6px;
    margin-bottom: 18px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--indigo-soft) !important;
    color: #c7d2fe !important;
}

/* ===================================================================
   RISK BADGE + RECOMMENDATION + CRISIS BANNER
   (preserved from PR1, refined to fit the new palette)
   =================================================================== */
.risk-badge {
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    font-size: 1.35rem;
    font-weight: 700;
    margin: 6px 0 16px 0;
    backdrop-filter: blur(10px);
    box-shadow: var(--shadow-card);
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.01em;
}
.risk-high {
    background: linear-gradient(135deg, rgba(244,63,94,0.22), rgba(244,63,94,0.06));
    border: 2px solid var(--rose);
    color: #fda4af;
}
.risk-medium {
    background: linear-gradient(135deg, rgba(245,158,11,0.22), rgba(245,158,11,0.06));
    border: 2px solid var(--amber);
    color: #fcd34d;
}
.risk-low {
    background: linear-gradient(135deg, rgba(16,185,129,0.22), rgba(16,185,129,0.06));
    border: 2px solid var(--emerald);
    color: #6ee7b7;
}

.rec-box {
    padding: 18px 22px;
    border-radius: 14px;
    margin: 12px 0;
    font-size: 0.96rem;
    line-height: 1.65;
    backdrop-filter: blur(10px);
}
.rec-high   { background: rgba(244,63,94,0.08); border-left: 4px solid var(--rose);   color: #fecdd3; }
.rec-medium { background: rgba(245,158,11,0.08); border-left: 4px solid var(--amber); color: #fde68a; }
.rec-low    { background: rgba(16,185,129,0.08); border-left: 4px solid var(--emerald); color: #a7f3d0; }

/* Crisis banner — emergency-first, ARIA-live, never collapses */
.crisis-banner {
    padding: 22px 24px;
    border-radius: 16px;
    margin: 0 0 18px 0;
    background: linear-gradient(135deg, rgba(244,63,94,0.20), rgba(244,63,94,0.07));
    border: 2px solid var(--rose);
    box-shadow: 0 12px 36px rgba(244,63,94,0.22);
    color: #ffe4e6;
}
.crisis-banner h3 { margin: 0 0 8px 0; color: #fda4af; font-size: 1.18rem; }
.crisis-banner p  { margin: 6px 0; line-height: 1.55; font-size: 0.96rem; }
.crisis-banner ul { margin: 8px 0 0 0; padding-left: 22px; }
.crisis-banner li { margin: 4px 0; font-size: 0.96rem; }
.crisis-banner a  { color: #fecdd3; text-decoration: underline; }

/* Onboarding card (Dashboard empty state) */
.onboard-card {
    padding: 44px 36px;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(34,211,238,0.06), rgba(99,102,241,0.06));
    border: 1px dashed var(--border-strong);
    text-align: center;
}
.onboard-card h2 { margin: 0 0 10px 0; }
.onboard-card p  { color: var(--text-muted); margin: 6px 0; }

/* ===================================================================
   FOOTER
   =================================================================== */
.sentinel-footer {
    margin-top: 56px;
    padding: 28px 24px 22px 24px;
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0.01));
    border: 1px solid var(--border);
}
.sentinel-footer .ftr-grid {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr;
    gap: 28px;
    margin-bottom: 18px;
}
@media (max-width: 800px) {
    .sentinel-footer .ftr-grid { grid-template-columns: 1fr; }
}
.sentinel-footer h5 {
    margin: 0 0 8px 0; font-size: 0.78rem; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--cyan); font-weight: 700;
}
.sentinel-footer p, .sentinel-footer li {
    color: var(--text-muted); font-size: 0.88rem; line-height: 1.55;
}
.sentinel-footer ul { list-style: none; padding: 0; margin: 0; }
.sentinel-footer li { margin: 4px 0; }
.sentinel-footer .disclaimer {
    margin-top: 16px; padding-top: 14px;
    border-top: 1px solid var(--border);
    font-size: 0.8rem; color: var(--text-dim);
    line-height: 1.55;
}
.sentinel-footer .disclaimer strong { color: var(--text-muted); }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def api_call(method: str, endpoint: str, **kwargs):
    """
    Make an HTTP request to the FastAPI backend with error handling.

    Args:
        method: HTTP method ("get", "post", "delete").
        endpoint: API endpoint path (e.g., "/api/checkin").
        **kwargs: Additional arguments passed to requests.

    Returns:
        Parsed JSON response or None on error.
    """
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = getattr(requests, method)(url, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend server. Is it running on port 8000?")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The server might be loading ML models — please wait and retry.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"Server error: {e.response.status_code} — {e.response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None


def get_risk_class(level: str) -> str:
    """Map risk level to CSS class name."""
    return {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}.get(level, "risk-low")


def get_rec_class(level: str) -> str:
    """Map risk level to recommendation CSS class."""
    return {"HIGH": "rec-high", "MEDIUM": "rec-medium", "LOW": "rec-low"}.get(level, "rec-low")


# ===========================================================================
# PLOTLY CHART THEME (dark-friendly, aligned with the new palette)
# ===========================================================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLOR_TEXT, family="Inter, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
)


# ===========================================================================
# NAVBAR
# ===========================================================================

def render_navbar() -> None:
    """Render the top brand bar + horizontal nav links.

    Streamlit doesn't expose a native top navigation, so we approximate one
    with a flex container holding the brand mark and a row of styled buttons.
    The active page is highlighted by wrapping its button in a div with the
    ``nav-active`` class (see CUSTOM_CSS).
    """
    active = st.session_state["page"]

    # Brand row + nav (logo on the left, nav on the right via st.columns).
    st.markdown('<div class="sentinel-navbar">', unsafe_allow_html=True)
    brand_col, nav_col = st.columns([1.4, 2.6], vertical_alignment="center")

    with brand_col:
        st.markdown(
            f"""
            <div class="sentinel-brand">
                <div class="logo">{SENTINEL_LOGO_SVG}</div>
                <div class="wordmark">
                    <span class="name">Sentinel</span>
                    <span class="tagline">Early Mental-Health Signals</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_col:
        st.markdown('<div class="sentinel-nav-row">', unsafe_allow_html=True)
        nav_cols = st.columns(len(PAGES))
        for col, page in zip(nav_cols, PAGES):
            with col:
                if page == active:
                    st.markdown('<div class="nav-active">', unsafe_allow_html=True)
                if st.button(page, key=f"nav_{page}", use_container_width=True):
                    _go_to(page)
                    st.rerun()
                if page == active:
                    st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# FOOTER (always visible — disclaimer + crisis hotlines)
# ===========================================================================

def render_footer() -> None:
    """Render the always-visible footer with crisis hotlines + disclaimer."""
    st.markdown(
        """
        <div class="sentinel-footer">
            <div class="ftr-grid">
                <div>
                    <h5>Sentinel</h5>
                    <p>Early mental-health signal detection through daily check-ins,
                    NLP analysis, and a safety screen that surfaces crisis resources
                    immediately when needed.</p>
                </div>
                <div>
                    <h5>Crisis hotlines</h5>
                    <ul>
                        <li><b>iCall (IN)</b> — 9152987821</li>
                        <li><b>AASRA (IN)</b> — 9820466726 (24/7)</li>
                        <li><b>988 Lifeline (US)</b> — call or text 988</li>
                        <li><b>Samaritans (UK)</b> — 116 123</li>
                    </ul>
                </div>
                <div>
                    <h5>About</h5>
                    <ul>
                        <li>Educational &amp; research use only</li>
                        <li>Not a clinical diagnostic tool</li>
                        <li>Built on FastAPI · Streamlit · XGBoost · DistilBERT</li>
                    </ul>
                </div>
            </div>
            <div class="disclaimer">
                <strong>Disclaimer.</strong> Sentinel is for educational and research
                purposes only and is <strong>not</strong> a clinical diagnostic tool.
                It does not provide medical advice, diagnosis, or treatment. If you are
                in crisis or experiencing a mental-health emergency, please contact a
                qualified professional or your local emergency services immediately.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# PAGE: HOME
# ===========================================================================

def render_home() -> None:
    """Hero, problem statement, solution pipeline, value props, CTA strip."""

    # ----- HERO -------------------------------------------------------
    st.markdown(
        """
        <div class="hero">
            <span class="eyebrow">🛡️ Sentinel · v0.1</span>
            <h1>Catch the <span class="accent">drift</span>, not just the&nbsp;crisis.</h1>
            <p class="lede">
                Most mental-health tools react after a crisis. Sentinel reads the
                slow signals — disrupted sleep, fading social contact, journals
                turning bleak — and surfaces them <strong>before</strong> things
                escalate, with a non-negotiable safety net for crisis language.
            </p>
            <div class="hero-meta">
                <span>Daily check-in in under 60 seconds</span>
                <span>Five weighted signals · explainable</span>
                <span>Crisis resources surface instantly</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Hero CTAs (rendered as Streamlit buttons so they trigger reruns)
    cta_a, cta_b, _ = st.columns([1, 1, 3])
    with cta_a:
        if st.button("Start your check-in", key="hero_cta_dash",
                     type="primary", use_container_width=True):
            _go_to("Dashboard")
            st.rerun()
    with cta_b:
        if st.button("How it works", key="hero_cta_solution",
                     type="secondary", use_container_width=True):
            _go_to("Solution")
            st.rerun()

    st.markdown("<div style='height: 36px'></div>", unsafe_allow_html=True)

    # ----- PROBLEM STATEMENT -----------------------------------------
    st.markdown(
        """
        <div class="section-eyebrow">The problem</div>
        <h2 class="section-title">Mental health doesn't break overnight — it drifts.</h2>
        <p class="section-lede">
            Symptoms typically begin years before someone seeks help. The earliest
            signals — sleep changes, withdrawal, mood shifts, bleaker self-talk —
            are exactly the kind of patterns a daily journal can capture, if
            something is paying attention.
        </p>
        """,
        unsafe_allow_html=True,
    )

    stat_cols = st.columns(4)
    stats = [
        ("1 in 8", "people globally live with a mental disorder",   "WHO, 2022"),
        ("75%",    "of mental-health conditions emerge before age 25", "NIH"),
        ("8–10 yr", "average gap between symptom onset and treatment", "NIMH"),
        ("4th",    "leading cause of death among 15–29 year olds (suicide)", "WHO"),
    ]
    for col, (val, label, source) in zip(stat_cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-value">{val}</div>
                    <div class="stat-label">{label}</div>
                    <div class="stat-source">Source: {source}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

    # ----- OUR SOLUTION (PIPELINE) -----------------------------------
    st.markdown(
        """
        <div class="section-eyebrow">Our solution</div>
        <h2 class="section-title">Five signals. One score. A safety net that never sleeps.</h2>
        <p class="section-lede">
            Sentinel reads sleep, mood, activity, social contact, and journal
            language together — then blends them into one weighted score with
            an unconditional crisis screen layered on top.
        </p>
        <div class="pipeline">
            <div class="pipe-step">
                <div class="pipe-num">1</div>
                <h4>Daily check-in</h4>
                <p>Sleep hours, mood (1–10), activity, social contact, optional journal — under a minute.</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">2</div>
                <h4>NLP &amp; anomaly</h4>
                <p>Journal sentiment, linguistic markers, and per-window deviation from your baseline.</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">3</div>
                <h4>Risk engine</h4>
                <p>Weighted blend of five components plus a phrase-based safety screen for crisis language.</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">4</div>
                <h4>Actionable result</h4>
                <p>Risk level, dominant factor, plain-language guidance — and crisis resources when needed.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

    # ----- WHY SENTINEL ----------------------------------------------
    st.markdown(
        """
        <div class="section-eyebrow">Why Sentinel</div>
        <h2 class="section-title">Designed to be honest, transparent, and safe-by-default.</h2>
        """,
        unsafe_allow_html=True,
    )

    feature_rows = [
        [
            ("🛡️", "Safety first",
             "A phrase-based screen for self-harm language unconditionally forces HIGH risk and surfaces crisis hotlines."),
            ("📊", "Holistic signal",
             "Five weighted components — never a single black-box number. You see exactly what drove the score."),
            ("🧠", "Contextual NLP",
             "Sentiment plus linguistic markers (1st-person ratio, absolutist language, negative-emotion ratio)."),
        ],
        [
            ("⚖️", "Adaptive scoring",
             "Weights re-normalise when journals or anomaly history aren't available — no silent under-scoring."),
            ("🚨", "Crisis-ready",
             "Helplines surface immediately on HIGH or any safety override, never buried behind an expander."),
            ("🔍", "Explainable",
             "Every component score, the dominant factor, and the recommendation are all visible to the user."),
        ],
    ]
    for row in feature_rows:
        cols = st.columns(3)
        for col, (icon, title, body) in zip(cols, row):
            with col:
                st.markdown(
                    f"""
                    <div class="card">
                        <div class="card-icon">{icon}</div>
                        <h4>{title}</h4>
                        <p>{body}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ----- CTA STRIP --------------------------------------------------
    st.markdown(
        """
        <div class="cta-strip">
            <div>
                <h3>Ready to try a check-in?</h3>
                <p>Takes under a minute. Your data stays in the local database.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cta_c, _ = st.columns([1, 4])
    with cta_c:
        if st.button("Open the dashboard →", key="cta_open_dash",
                     type="primary", use_container_width=True):
            _go_to("Dashboard")
            st.rerun()


# ===========================================================================
# PAGE: ABOUT
# ===========================================================================

def render_about() -> None:
    st.markdown(
        """
        <div class="section-eyebrow">About Sentinel</div>
        <h2 class="section-title">Catch the drift, not just the crisis.</h2>
        <p class="section-lede">
            Sentinel is a research-grade prototype for surfacing early
            mental-health risk through everyday self-reported signals. It
            isn't a diagnostic tool — it's a lens. The goal is to make the
            invisible drift between "I'm fine" and "I need help" a little
            more visible, a little earlier.
        </p>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    pillars = [
        ("🎯", "Mission",
         "Make early mental-health signals legible — for the user themselves first, "
         "and for clinicians second when consent allows."),
        ("👁️", "Vision",
         "A future where slow drift gets a friendly nudge weeks before it would "
         "have become a crisis, without surveillance and without diagnosis."),
        ("⚖️", "Ethos",
         "Safety-by-default. Explainability over accuracy theatre. The user sees "
         "every signal that drove their score — no hidden judgements."),
    ]
    for col, (icon, title, body) in zip(cols, pillars):
        with col:
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-icon">{icon}</div>
                    <h4>{title}</h4>
                    <p>{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 36px'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-eyebrow">Design principles</div>
        <h3 style="margin-top:0;">What Sentinel will and won't do</h3>
        """,
        unsafe_allow_html=True,
    )

    will_col, wont_col = st.columns(2)
    with will_col:
        st.markdown(
            """
            <div class="card">
                <div class="card-icon">✓</div>
                <h4>Sentinel <em>will</em></h4>
                <p>
                    • Track five behavioural and linguistic signals over time<br/>
                    • Show every component score, never a single opaque number<br/>
                    • Force HIGH risk on crisis language, no matter the other inputs<br/>
                    • Surface crisis hotlines immediately when they're needed<br/>
                    • Let you export your own history at any time
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with wont_col:
        st.markdown(
            """
            <div class="card">
                <div class="card-icon">✗</div>
                <h4>Sentinel <em>will not</em></h4>
                <p>
                    • Diagnose any condition or replace a clinician<br/>
                    • Echo a user's self-harm wording back at them<br/>
                    • Train on your data without an explicit opt-in<br/>
                    • Hide its reasoning behind a single black-box score<br/>
                    • Suppress crisis resources to keep the UI clean
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ===========================================================================
# PAGE: SOLUTION
# ===========================================================================

def render_solution() -> None:
    st.markdown(
        """
        <div class="section-eyebrow">How Sentinel works</div>
        <h2 class="section-title">From a 60-second check-in to an explainable risk score.</h2>
        <p class="section-lede">
            The pipeline is intentionally simple — five signals, one weighted
            blend, and a non-negotiable safety screen. Every step is auditable
            from the dashboard, and every score is visible to the user.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # --- Pipeline diagram (re-used from Home) ----------------------
    st.markdown(
        """
        <div class="pipeline">
            <div class="pipe-step">
                <div class="pipe-num">1</div>
                <h4>Inputs</h4>
                <p>Sleep hours, mood (1–10), activity level, social contact count, journal text (optional).</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">2</div>
                <h4>Feature engineering</h4>
                <p>Normalise each signal to a 0–1 risk component; compute rolling deviations from baseline.</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">3</div>
                <h4>NLP analysis</h4>
                <p>Sentiment + linguistic markers — first-person ratio, absolutist language, negative-emotion ratio.</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">4</div>
                <h4>Anomaly detector</h4>
                <p>Isolation Forest flags samples that deviate from the population baseline (per-user is on the roadmap).</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">5</div>
                <h4>Weighted risk score</h4>
                <p>Five components combined with re-normalised weights when NLP or anomaly aren't available.</p>
            </div>
            <div class="pipe-step">
                <div class="pipe-num">6</div>
                <h4>Safety screen</h4>
                <p>Phrase-based detector for crisis language. If matched, risk is forced to HIGH, no exceptions.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)

    # --- Component weights ---------------------------------------
    st.markdown(
        """
        <div class="section-eyebrow">Risk weights</div>
        <h3 style="margin-top:0;">How the components combine</h3>
        <p class="section-lede">
            Default weights (tuned on synthetic data — not a clinical instrument).
            When NLP or anomaly signals aren't available, the remaining weights
            re-normalise to 1.0 so users without journals or short history aren't
            silently under-scored.
        </p>
        """,
        unsafe_allow_html=True,
    )

    weight_data = [
        ("Sleep",    0.20, COLOR_CYAN),
        ("Mood",     0.25, COLOR_INDIGO),
        ("Activity", 0.10, COLOR_TEAL),
        ("Social",   0.15, COLOR_AMBER),
        ("NLP",      0.20, "#a78bfa"),
        ("Anomaly",  0.10, COLOR_ROSE),
    ]
    fig = go.Figure(go.Bar(
        x=[v for _, v, _ in weight_data],
        y=[k for k, _, _ in weight_data],
        orientation="h",
        marker=dict(color=[c for _, _, c in weight_data], opacity=0.85),
        text=[f"{v:.0%}" for _, v, _ in weight_data],
        textposition="outside",
        textfont=dict(color=COLOR_TEXT, size=13),
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(
        height=320,
        xaxis=dict(range=[0, 0.32], title="Weight", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        title=dict(text="Default component weights", font=dict(size=15)),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)

    # --- Safety screen ---------------------------------------------
    st.markdown(
        """
        <div class="card" style="border-color: rgba(244,63,94,0.36);
                                  background: linear-gradient(135deg,
                                  rgba(244,63,94,0.10), rgba(244,63,94,0.03));">
            <div class="card-icon" style="background: rgba(244,63,94,0.18); color: #fda4af;">🛡️</div>
            <h4>The safety screen — non-negotiable</h4>
            <p>
                Before any blending happens, the journal text is checked for
                phrases associated with active suicidal ideation, self-harm,
                or planning. The list includes negation handling so
                <em>"I would never want to die"</em> doesn't trigger.
                If a phrase matches, the risk level is forced to <strong>HIGH</strong>
                regardless of how good the sleep / mood / social numbers look,
                and crisis hotlines surface immediately above the assessment.
                The matched phrases are logged but never echoed back to the user.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# PAGE: RESOURCES
# ===========================================================================

def render_resources() -> None:
    st.markdown(
        """
        <div class="section-eyebrow">Resources</div>
        <h2 class="section-title">If you need someone to talk to right now.</h2>
        <p class="section-lede">
            You don't need to be in immediate danger to call a crisis line.
            They are trained to listen — even if you're "just" overwhelmed,
            isolated, or scared.
        </p>
        """,
        unsafe_allow_html=True,
    )

    helplines = [
        ("🇮🇳 iCall (India)",
         "9152987821",
         "Mon–Sat, 8am–10pm. Free, confidential, multilingual support."),
        ("🇮🇳 AASRA (India)",
         "9820466726",
         "24/7 helpline for emotional distress and suicide prevention."),
        ("🇮🇳 Vandrevala Foundation",
         "1860-2662-345",
         "24/7 mental-health helpline."),
        ("🇺🇸 988 Suicide & Crisis Lifeline",
         "Call or text 988",
         "24/7 free, confidential support across the United States."),
        ("🇺🇸 Crisis Text Line",
         "Text HOME to 741741",
         "Free, 24/7 text-based support in the US, UK, Canada, Ireland."),
        ("🇬🇧 Samaritans",
         "116 123",
         "Free 24/7 support across the UK and Republic of Ireland."),
    ]

    rows = [helplines[i:i + 3] for i in range(0, len(helplines), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, (name, number, desc) in zip(cols, row):
            with col:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>{name}</h4>
                        <p style="color: var(--text); font-weight: 600; margin: 4px 0 8px 0;">
                            {number}
                        </p>
                        <p>{desc}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height: 36px'></div>", unsafe_allow_html=True)

    # --- When to seek help -----------------------------------------
    st.markdown(
        """
        <div class="section-eyebrow">When to reach out</div>
        <h3 style="margin-top:0;">Signals worth taking seriously</h3>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    with cols[0]:
        st.markdown(
            """
            <div class="card">
                <h4>Reach out today if any of these are true</h4>
                <p>
                    • You're having thoughts of suicide or self-harm<br/>
                    • You feel like a burden to others<br/>
                    • You're using substances to cope<br/>
                    • You're isolating from people who care about you<br/>
                    • You can't sleep, or you're sleeping all day
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            """
            <div class="card">
                <h4>Worth checking in with a professional</h4>
                <p>
                    • Persistent low mood for two weeks or more<br/>
                    • Loss of interest in things you used to enjoy<br/>
                    • Physical symptoms with no clear cause<br/>
                    • Anxiety that's interfering with daily life<br/>
                    • Trouble concentrating or making decisions
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card" style="text-align:center;
                                  background: linear-gradient(135deg,
                                  rgba(34,211,238,0.08), rgba(99,102,241,0.06));
                                  border-color: rgba(34,211,238,0.24);">
            <h4 style="margin: 0 0 6px 0;">International directory</h4>
            <p>
                <a href="https://www.iasp.info/resources/Crisis_Centres/"
                   target="_blank" rel="noopener" style="color:#67e8f9;">
                    IASP — Crisis centres around the world
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# PAGE: DASHBOARD
# ===========================================================================

def render_dashboard() -> None:
    """Sidebar check-in form + the original 3 tabs (Today / Trends / History)."""

    # ----- Sidebar form --------------------------------------------
    submitted = False
    user_id = "user_001"

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sentinel-brand" style="margin-bottom: 16px;">
                <div class="logo">{SENTINEL_LOGO_SVG}</div>
                <div class="wordmark">
                    <span class="name">Sentinel</span>
                    <span class="tagline">Daily check-in</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        user_id = st.text_input(
            "User ID",
            value="user_001",
            help="Unique identifier — keeps your history separate from other users.",
        )

        st.markdown("---")

        with st.expander("Daily check-in form", expanded=True):
            sleep_hours = st.slider(
                "😴 Sleep hours",
                min_value=0.0, max_value=12.0, value=7.0, step=0.5,
                help="How many hours did you sleep last night?",
            )
            mood_score = st.slider(
                "🎭 Mood score",
                min_value=1, max_value=10, value=6,
                help="Rate your overall mood today (1 = worst, 10 = best).",
            )
            activity_level = st.selectbox(
                "🏃 Activity level",
                options=["sedentary", "light", "moderate", "active"],
                index=1,
            )
            social_interactions = st.number_input(
                "🤝 Social interactions",
                min_value=0, max_value=30, value=3,
                help="Count of meaningful conversations or social contacts today.",
            )
            journal_text = st.text_area(
                "📓 Journal entry",
                placeholder="Write anything about your day, how you're feeling, what's on your mind…",
                height=120,
                help="Optional — used for NLP-based sentiment + linguistic analysis.",
            )

            submitted = st.button(
                "Submit check-in",
                type="primary",
                use_container_width=True,
            )

        st.markdown("---")

        demo_mode = st.button(
            "🎬 Demo mode (high-risk)",
            use_container_width=True,
            help="Pre-fills with a high-risk scenario for demonstration purposes.",
        )
        if demo_mode:
            demo_payload = {
                "user_id": user_id,
                "sleep_hours": 3.5,
                "mood_score": 2,
                "activity_level": "sedentary",
                "social_interactions": 0,
                "journal_text": (
                    "I can't sleep at all. Everything feels meaningless and hopeless. "
                    "I'm completely alone and nothing ever gets better. I'm so tired "
                    "of feeling worthless and empty. I never want to talk to anyone."
                ),
            }
            with st.spinner("Running high-risk demo assessment…"):
                demo_result = api_call("post", "/api/checkin", json=demo_payload)
            if demo_result:
                st.session_state["latest_result"] = demo_result
                st.success("Demo check-in submitted.")
                st.rerun()

        stats = api_call("get", f"/api/stats/{user_id}")
        if stats:
            st.metric("📅 Days tracked", stats.get("total_days", 0))

    # ----- Submission ----------------------------------------------
    if submitted:
        payload = {
            "user_id": user_id,
            "sleep_hours": sleep_hours,
            "mood_score": mood_score,
            "activity_level": activity_level,
            "social_interactions": social_interactions,
            "journal_text": journal_text if journal_text else None,
        }
        with st.spinner("Analyzing your check-in with the ML pipeline…"):
            result = api_call("post", "/api/checkin", json=payload)
        if result:
            st.session_state["latest_result"] = result
            st.rerun()

    # ----- Page header ---------------------------------------------
    st.markdown(
        """
        <div class="section-eyebrow">Dashboard</div>
        <h2 class="section-title">Your latest check-in &amp; trends</h2>
        <p class="section-lede">
            Submit a check-in from the sidebar. Today's assessment, your seven-day
            trends, and your full history are all available below.
        </p>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Today's assessment", "7-day trends", "History log"])

    # ----- Tab 1: today --------------------------------------------
    with tab1:
        result = st.session_state.get("latest_result")
        if result:
            _render_assessment(result)
        else:
            st.markdown(
                """
                <div class="onboard-card">
                    <h2>Welcome to your Sentinel dashboard</h2>
                    <p>
                        Submit your first check-in using the form in the sidebar to
                        receive your personalised, AI-assisted risk assessment.
                    </p>
                    <p>
                        Want to preview a high-risk scenario? Click
                        <strong>🎬 Demo mode</strong> in the sidebar.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ----- Tab 2: 7-day trends -------------------------------------
    with tab2:
        _render_trends(user_id)

    # ----- Tab 3: history log --------------------------------------
    with tab3:
        _render_history(user_id)


# --- Helper renderers (Dashboard tabs) ------------------------------------

def _render_assessment(result: dict) -> None:
    """Render the 'Today's assessment' tab body."""
    risk_level = result.get("risk_level", "LOW")
    risk_score = result.get("risk_score", 0.0)
    component_scores = result.get("component_scores", {})
    recommendation = result.get("recommendation", "")
    nlp_analysis = result.get("nlp_analysis", {})
    anomaly_detected = result.get("anomaly_detected", False)
    dominant_factor = result.get("dominant_factor", "N/A")
    safety_override = bool(result.get("safety_override", False))

    # Crisis banner above everything when HIGH or safety override
    if safety_override or risk_level == "HIGH":
        heading = (
            "🚨 We're concerned about what you've shared"
            if safety_override
            else "🚨 Your check-in indicates HIGH risk — please reach out"
        )
        opening = (
            "Your journal entry contains language that suggests you may be "
            "struggling with thoughts of self-harm. You are not alone, and "
            "help is available right now."
            if safety_override
            else "Several signals from your check-in suggest you may be "
            "struggling. Please consider reaching out to someone you trust "
            "or a crisis line today."
        )
        st.markdown(
            f"""
            <div class="crisis-banner" role="alert" aria-live="assertive">
                <h3>{heading}</h3>
                <p>{opening}</p>
                <ul>
                    <li>🇮🇳 <b>iCall</b> — 9152987821 (Mon–Sat, 8am–10pm)</li>
                    <li>🇮🇳 <b>AASRA</b> — 9820466726 (24/7)</li>
                    <li>🇺🇸 <b>988 Suicide &amp; Crisis Lifeline</b> — call or text 988</li>
                    <li>🇬🇧 <b>Samaritans</b> — 116 123</li>
                </ul>
                <p style="margin-top:10px;"><b>If you are in immediate danger,
                please call your local emergency services.</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Risk badge
    badge_class = get_risk_class(risk_level)
    st.markdown(
        f'<div class="risk-badge {badge_class}">'
        f'Risk level · {risk_level} &nbsp;·&nbsp; Score {risk_score:.2f}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk level", risk_level)
    col2.metric("Risk score", f"{risk_score:.3f}")
    col3.metric("Dominant factor", dominant_factor.upper())
    col4.metric("Anomaly", "YES" if anomaly_detected else "NO")

    st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)

    # Component scores chart
    st.markdown("#### Component risk scores")
    if component_scores:
        components = list(component_scores.keys())
        scores = list(component_scores.values())
        colors = [COLOR_ROSE if s >= 0.65 else COLOR_AMBER if s >= 0.35 else "#10b981"
                  for s in scores]

        fig = go.Figure(go.Bar(
            x=scores,
            y=[c.upper() for c in components],
            orientation="h",
            marker=dict(color=colors, opacity=0.88, line=dict(width=0)),
            text=[f"{s:.2f}" for s in scores],
            textposition="outside",
            textfont=dict(color=COLOR_TEXT, size=13),
        ))
        fig.update_layout(**PLOTLY_LAYOUT)
        fig.update_layout(
            height=300,
            xaxis=dict(range=[0, 1.1], title="Risk score (0 = low, 1 = high)"),
            title=dict(text="Component breakdown", font=dict(size=15)),
        )
        fig.add_vline(x=0.65, line_dash="dash", line_color="rgba(244,63,94,0.5)",
                      annotation_text="HIGH", annotation_font_color="#fda4af")
        fig.add_vline(x=0.35, line_dash="dash", line_color="rgba(245,158,11,0.5)",
                      annotation_text="MEDIUM", annotation_font_color="#fcd34d")
        st.plotly_chart(fig, use_container_width=True)

    # Recommendation
    st.markdown("#### Recommendation")
    rec_class = get_rec_class(risk_level)
    st.markdown(
        f'<div class="rec-box {rec_class}">{recommendation}</div>',
        unsafe_allow_html=True,
    )

    # NLP analysis
    with st.expander("NLP journal analysis", expanded=False):
        if nlp_analysis.get("status") == "no_journal":
            st.info("No journal text was provided for this check-in.")
        else:
            ncol1, ncol2, ncol3, ncol4 = st.columns(4)
            ncol1.metric("Sentiment", nlp_analysis.get("sentiment_label", "N/A"))
            ncol2.metric("Confidence", f"{nlp_analysis.get('sentiment_confidence', 0):.0%}")
            ncol3.metric("NLP risk", f"{nlp_analysis.get('nlp_risk_score', 0):.3f}")
            ncol4.metric("Word count", nlp_analysis.get("text_length", 0))

            st.markdown("##### Linguistic markers")
            lcol1, lcol2, lcol3 = st.columns(3)
            lcol1.metric("1st-person ratio", f"{nlp_analysis.get('first_person_ratio', 0):.3f}")
            lcol2.metric("Absolutist ratio", f"{nlp_analysis.get('absolutist_ratio', 0):.3f}")
            lcol3.metric("Neg. emotion ratio", f"{nlp_analysis.get('negative_emotion_ratio', 0):.3f}")

    if anomaly_detected:
        st.warning(
            "Behavioural anomaly detected — your recent patterns deviate "
            "significantly from your established baseline. This doesn't necessarily "
            "mean something is wrong, but it's worth reflecting on recent changes."
        )


def _render_trends(user_id: str) -> None:
    """Render the '7-day trends' tab body."""
    st.markdown("#### 7-day behavioural trends")

    history = api_call("get", f"/api/history/{user_id}?days=7")
    if not (history and history.get("total_records", 0) > 0):
        st.info("No check-in data yet. Submit your first check-in to see trends.")
        return

    df = pd.DataFrame(history["records"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Mood
    fig_mood = go.Figure()
    fig_mood.add_trace(go.Scatter(
        x=df["timestamp"], y=df["mood_score"],
        mode="lines+markers", name="Mood score",
        line=dict(color=COLOR_INDIGO, width=3),
        marker=dict(size=10, symbol="circle"),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.10)",
    ))
    fig_mood.update_layout(**PLOTLY_LAYOUT)
    fig_mood.update_layout(
        title=dict(text="🎭 Mood score (1–10)", font=dict(size=15)),
        yaxis=dict(range=[0, 11]), height=320,
    )
    st.plotly_chart(fig_mood, use_container_width=True)

    # Sleep
    fig_sleep = go.Figure()
    fig_sleep.add_trace(go.Scatter(
        x=df["timestamp"], y=df["sleep_hours"],
        mode="lines+markers", name="Sleep hours",
        line=dict(color=COLOR_CYAN, width=3),
        marker=dict(size=10, symbol="diamond"),
        fill="tozeroy", fillcolor="rgba(34,211,238,0.10)",
    ))
    fig_sleep.add_hline(y=7, line_dash="dash", line_color="rgba(16,185,129,0.5)",
                       annotation_text="7hr minimum", annotation_font_color="#6ee7b7")
    fig_sleep.update_layout(**PLOTLY_LAYOUT)
    fig_sleep.update_layout(
        title=dict(text="😴 Sleep hours (0–12)", font=dict(size=15)),
        yaxis=dict(range=[0, 13]), height=320,
    )
    st.plotly_chart(fig_sleep, use_container_width=True)

    # Social
    bar_colors = [COLOR_ROSE if v <= 1 else COLOR_AMBER if v <= 3 else "#10b981"
                  for v in df["social_interactions"]]
    fig_social = go.Figure(go.Bar(
        x=df["timestamp"], y=df["social_interactions"],
        marker=dict(color=bar_colors, opacity=0.88),
        text=df["social_interactions"], textposition="outside",
        textfont=dict(color=COLOR_TEXT),
    ))
    fig_social.update_layout(**PLOTLY_LAYOUT)
    fig_social.update_layout(
        title=dict(text="🤝 Social interactions per day", font=dict(size=15)),
        height=320,
    )
    st.plotly_chart(fig_social, use_container_width=True)

    # Risk
    risk_df = df[df["risk_score"].notna()].copy()
    if len(risk_df) > 0:
        fig_risk = go.Figure()
        fig_risk.add_hrect(y0=0.65, y1=1.0, fillcolor="rgba(244,63,94,0.08)",
                          line_width=0, annotation_text="HIGH",
                          annotation_font_color="rgba(244,63,94,0.55)")
        fig_risk.add_hrect(y0=0.35, y1=0.65, fillcolor="rgba(245,158,11,0.06)",
                          line_width=0, annotation_text="MEDIUM",
                          annotation_font_color="rgba(245,158,11,0.55)")
        fig_risk.add_hrect(y0=0.0, y1=0.35, fillcolor="rgba(16,185,129,0.06)",
                          line_width=0, annotation_text="LOW",
                          annotation_font_color="rgba(16,185,129,0.55)")
        fig_risk.add_trace(go.Scatter(
            x=risk_df["timestamp"], y=risk_df["risk_score"],
            mode="lines+markers", name="Risk score",
            line=dict(color="#fb7185", width=3),
            marker=dict(size=10, symbol="star"),
        ))
        fig_risk.update_layout(**PLOTLY_LAYOUT)
        fig_risk.update_layout(
            title=dict(text="⚡ Risk score trend (0–1)", font=dict(size=15)),
            yaxis=dict(range=[0, 1.05]), height=350,
        )
        st.plotly_chart(fig_risk, use_container_width=True)


def _render_history(user_id: str) -> None:
    """Render the 'History log' tab body."""
    st.markdown("#### Check-in history (last 30 days)")

    history_30 = api_call("get", f"/api/history/{user_id}?days=30")
    if not (history_30 and history_30.get("total_records", 0) > 0):
        st.info("No history yet. Start checking in to build your history.")
        return

    df_hist = pd.DataFrame(history_30["records"])
    df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])

    scol1, scol2, scol3, scol4 = st.columns(4)
    avg_risk = df_hist["risk_score"].mean() if df_hist["risk_score"].notna().any() else 0
    scol1.metric("📊 Avg risk score", f"{avg_risk:.3f}")
    scol2.metric("📅 Total days", len(df_hist))

    # LOW-risk streak (consecutive most-recent days at LOW)
    streak = 0
    for _, row in df_hist.sort_values("timestamp", ascending=False).iterrows():
        if row.get("risk_level") == "LOW":
            streak += 1
        else:
            break
    scol3.metric("🔥 LOW-risk streak", f"{streak} d")

    avg_mood = df_hist["mood_score"].mean() if "mood_score" in df_hist else 0
    scol4.metric("🎭 Avg mood", f"{avg_mood:.1f}")

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    display_cols = [
        "timestamp", "sleep_hours", "mood_score", "activity_level",
        "social_interactions", "risk_score", "risk_level",
    ]
    available = [c for c in display_cols if c in df_hist.columns]
    df_display = df_hist[available].copy()
    df_display["timestamp"] = df_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)

    csv_data = df_hist.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv_data,
        file_name=f"sentinel_history_{user_id}_{datetime.date.today()}.csv",
        mime="text/csv",
    )


# ===========================================================================
# MAIN — top-level routing
# ===========================================================================

render_navbar()

active_page = st.session_state["page"]
if active_page == "Home":
    render_home()
elif active_page == "Dashboard":
    render_dashboard()
elif active_page == "About":
    render_about()
elif active_page == "Solution":
    render_solution()
elif active_page == "Resources":
    render_resources()
else:
    # Defensive fallback: unknown page → reset to Home.
    st.session_state["page"] = DEFAULT_PAGE
    render_home()

render_footer()
