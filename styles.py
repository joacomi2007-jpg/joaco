# styles.py
"""
Inyecta CSS personalizado en la app Streamlit con soporte para tema claro/oscuro.
"""
import streamlit as st

CSS_DARK = """
<style>
/* ── TEMA OSCURO ──────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #0f1117;
}
[data-testid="stSidebar"] {
    background: #161b27;
    border-right: 1px solid #2a2f3d;
}

/* ── Tarjetas de métricas ──────────────────────────── */
[data-testid="stMetric"] {
    background: #1a1f2e;
    border: 1px solid #2a2f3d;
    border-radius: 10px;
    padding: 14px 18px !important;
    transition: border-color 0.2s;
}
[data-testid="stMetric"]:hover {
    border-color: #4f8ef7;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8892a4 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 700;
    color: #e8ecf4 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.82rem !important;
}

/* ── Tabs ──────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #161b27;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border-bottom: none;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px;
    color: #8892a4;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 7px 18px;
    border: none;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #2a3650 !important;
    color: #4f8ef7 !important;
}

/* ── Botones primarios ─────────────────────────────── */
[data-testid="baseButton-primary"], .stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: opacity 0.2s, transform 0.1s;
}
.stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* ── DataFrames / Tablas ───────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2f3d;
    border-radius: 8px;
}

/* ── Inputs ────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stNumberInput"] input {
    background: #1a1f2e !important;
    border-color: #2a2f3d !important;
    color: #e8ecf4 !important;
    border-radius: 8px !important;
}

/* ── Sliders ───────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #4f8ef7;
}

/* ── Cards de veredicto IA ─────────────────────────── */
.ia-card {
    background: #1a1f2e;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid #2a2f3d;
    margin-top: 8px;
}
.ia-card h3 {
    margin: 0 0 12px 0;
    font-size: 1rem;
    color: #8892a4;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Expanders ─────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #1a1f2e;
    border: 1px solid #2a2f3d;
    border-radius: 8px;
}

/* ── Subheaders personalizados ─────────────────────── */
.section-header {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4f8ef7;
    font-weight: 700;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid #2a2f3d;
    margin-bottom: 10px;
}

/* ── Advertencia de datos viejos ─────────────────────── */
.stale-warning {
    background: #292214;
    border-left: 3px solid #f59e0b;
    padding: 8px 12px;
    border-radius: 0 6px 6px 0;
    font-size: 0.82rem;
    color: #fcd34d;
}
</style>
"""

CSS_LIGHT = """
<style>
/* ── TEMA CLARO ───────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #ffffff;
}
[data-testid="stSidebar"] {
    background: #f8f9fa;
    border-right: 1px solid #dee2e6;
}

/* ── Tarjetas de métricas ──────────────────────────── */
[data-testid="stMetric"] {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 14px 18px !important;
    transition: border-color 0.2s;
}
[data-testid="stMetric"]:hover {
    border-color: #2563eb;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6c757d !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 700;
    color: #212529 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.82rem !important;
}

/* ── Tabs ──────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border-bottom: none;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px;
    color: #6c757d;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 7px 18px;
    border: none;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #e9ecef !important;
    color: #2563eb !important;
}

/* ── Botones primarios ─────────────────────────────── */
[data-testid="baseButton-primary"], .stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: opacity 0.2s, transform 0.1s;
}
.stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* ── DataFrames / Tablas ───────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #dee2e6;
    border-radius: 8px;
}

/* ── Inputs ────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    border-color: #dee2e6 !important;
    color: #212529 !important;
    border-radius: 8px !important;
}

/* ── Sliders ───────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #2563eb;
}

/* ── Cards de veredicto IA ─────────────────────────── */
.ia-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid #dee2e6;
    margin-top: 8px;
}
.ia-card h3 {
    margin: 0 0 12px 0;
    font-size: 1rem;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Expanders ─────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
}

/* ── Subheaders personalizados ─────────────────────── */
.section-header {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #2563eb;
    font-weight: 700;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid #dee2e6;
    margin-bottom: 10px;
}

/* ── Advertencia de datos viejos ─────────────────────── */
.stale-warning {
    background: #fff3cd;
    border-left: 3px solid #ffc107;
    padding: 8px 12px;
    border-radius: 0 6px 6px 0;
    font-size: 0.82rem;
    color: #856404;
}
</style>
"""

# Componentes CSS compartidos (no cambian con el tema)
CSS_SHARED = """
<style>
/* ── Badges de fuentes de datos ─────────────────────── */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 4px;
}
.badge-yahoo    { background: #1e3a5f; color: #60a5fa; }
.badge-fmp      { background: #14532d; color: #4ade80; }
.badge-av       { background: #3b1f6e; color: #c084fc; }
.badge-finnhub  { background: #7c2d12; color: #fb923c; }
.badge-stale    { background: #44403c; color: #d6d3d1; }

/* ── Veredictos IA ─────────────────────────────────── */
.veredicto-COMPRAR    { color: #22c55e; font-size: 1.6rem; font-weight: 800; }
.veredicto-REFORZAR   { color: #84cc16; font-size: 1.6rem; font-weight: 800; }
.veredicto-MANTENER   { color: #f59e0b; font-size: 1.6rem; font-weight: 800; }
.veredicto-REDUCIR    { color: #f97316; font-size: 1.6rem; font-weight: 800; }
.veredicto-VENDER     { color: #ef4444; font-size: 1.6rem; font-weight: 800; }
.veredicto-ERROR      { color: #6b7280; font-size: 1.6rem; font-weight: 800; }
</style>
"""

def inject_css():
    # Leer tema del session_state (por defecto oscuro)
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Oscuro"
    
    css = CSS_DARK if st.session_state.theme_mode == "Oscuro" else CSS_LIGHT
    st.markdown(css + CSS_SHARED, unsafe_allow_html=True)


def badge(source: str) -> str:
    css = {
        "Yahoo":       "badge-yahoo",
        "FMP":         "badge-fmp",
        "AlphaVantage":"badge-av",
        "Finnhub":     "badge-finnhub",
        "stale":       "badge-stale",
    }
    cls = css.get(source, "badge-av")
    return f'<span class="badge {cls}">{source}</span>'


def veredicto_badge(v: str) -> str:
    icons = {
        "COMPRAR": "🟢", "REFORZAR": "🔵",
        "MANTENER": "🟡", "REDUCIR": "🟠", "VENDER": "🔴"
    }
    icon = icons.get(v, "⚪")
    cls  = f"veredicto-{v}" if v in icons else "veredicto-ERROR"
    return f'<span class="{cls}">{icon} {v}</span>'