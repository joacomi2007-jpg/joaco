# app.py
import streamlit as st
import pandas as pd
import os

from ui_portfolio  import render_tab_portfolio
from ui_fundamental import render_tab_fundamental
from ui_radar      import render_tab_radar
from ui_analysis   import render_tab_analysis
from ui_analistas  import render_tab_analistas
from ui_ia         import render_tab_ia
from ui_charts     import render_tab_charts
from styles        import inject_css

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Terminal Pro Investor",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏦",
)

inject_css()

# ---------------------------------------------------------------------------
# 2. BARRA LATERAL
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Panel de Control")

    if st.button("🗑️ Limpiar Caché Streamlit", use_container_width=True):
        st.cache_data.clear()
        st.success("Caché de Streamlit limpiada.")

    st.divider()

    # Estado de APIs
    st.markdown("**🔌 Estado de APIs**")
    try:
        has_groq    = bool(st.secrets.get("GROQ_KEY",     ""))
        has_fmp     = bool(st.secrets.get("FMP_KEY",      ""))
        has_av      = bool(st.secrets.get("AV_KEYS",      []))
        has_finnhub = bool(st.secrets.get("FINNHUB_KEY",  ""))
    except Exception:
        has_groq = has_fmp = has_av = has_finnhub = False

    st.markdown(f"{'✅' if has_groq    else '❌'} Groq (IA)")
    st.markdown(f"{'✅' if has_fmp     else '❌'} FMP (Fundamental)")
    st.markdown(f"{'✅' if has_av      else '❌'} Alpha Vantage")
    st.markdown(f"{'✅' if has_finnhub else '❌'} Finnhub")

    if not any([has_groq, has_fmp, has_av]):
        st.warning(
            "Configurá tus claves en `.streamlit/secrets.toml`",
            icon="🔑"
        )

    st.divider()

    # Estadísticas de caché
    from cache_manager import list_cached_tickers
    cached = list_cached_tickers()
    st.metric("💾 Tickers en caché", len(cached))
    if cached:
        with st.expander("Ver tickers cacheados"):
            st.caption(", ".join(sorted(cached)[:50]))

    st.divider()
    st.caption("Terminal Pro Investor · v2.0\nDatos: Yahoo · FMP · AV · Finnhub")

# ---------------------------------------------------------------------------
# 3. PERSISTENCIA DEL PORTAFOLIO
# ---------------------------------------------------------------------------
if "mi_portfolio" not in st.session_state:
    if os.path.exists("portfolio.csv"):
        try:
            st.session_state.mi_portfolio = pd.read_csv("portfolio.csv")
        except Exception:
            st.session_state.mi_portfolio = pd.DataFrame([
                {"Ticker": "NVDA", "Cant": 1.0, "Costo ARS": 11000.0}
            ])
    else:
        st.session_state.mi_portfolio = pd.DataFrame([
            {"Ticker": "NVDA", "Cant": 1.0, "Costo ARS": 11000.0}
        ])

# ---------------------------------------------------------------------------
# 4. TÍTULO
# ---------------------------------------------------------------------------
st.markdown("# 🏦 Terminal Pro Investor")

# ---------------------------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "💼 Portafolio",
    "🏛️ Análisis Fundamental",
    "📉 Gráficos",
    "🎯 Radar Líderes",
    "📊 Análisis Cartera",
    "📈 Analistas",
    "💬 IA",
])

with tabs[0]: render_tab_portfolio()
with tabs[1]: render_tab_fundamental()
with tabs[2]: render_tab_charts()
with tabs[3]: render_tab_radar()
with tabs[4]: render_tab_analysis()
with tabs[5]: render_tab_analistas()
with tabs[6]: render_tab_ia()