# ui_analistas.py
"""
Pestaña de recomendaciones de analistas de Wall Street.
Fuente primaria: FMP (Financial Modeling Prep) — mucho más confiable que Yahoo en modo batch.
Fuente de respaldo: Yahoo Finance (para tickers no encontrados en FMP).
Los resultados se cachean localmente para evitar re-consultar la API.
"""
import streamlit as st
import pandas as pd
import yfinance as yf
import time
import requests
import os
from sp500_data import get_sp500_tickers
from cache_manager import get_cached, set_cache

# ── Helpers ─────────────────────────────────────────────────────────────────
def _fmp_key() -> str:
    try:
        return st.secrets.get("FMP_KEY", "")
    except Exception:
        return os.environ.get("FMP_KEY", "")

def _get_analyst_data_fmp(ticker: str, fmp_key: str) -> dict | None:
    """Obtiene target price y consenso de analistas vía FMP."""
    try:
        r = requests.get(
            f"https://financialmodelingprep.com/api/v3/analyst-price-targets"
            f"?symbol={ticker}&page=0&apikey={fmp_key}",
            timeout=5
        ).json()
        if not r or not isinstance(r, list):
            return None

        recents = r[:20]
        targets = [float(x["priceTarget"]) for x in recents
                   if x.get("priceTarget") not in (None, 0, "")]
        precio = next(
            (float(x["priceWhenPosted"]) for x in recents
             if x.get("priceWhenPosted") not in (None, 0, "")),
            None
        )
        if not targets or not precio or precio == 0:
            return None

        median_t = sorted(targets)[len(targets) // 2]
        upside   = round(((median_t / precio) - 1) * 100, 2)
        if upside <= 0:
            return None

        # Empresa
        name = ticker
        try:
            prof = requests.get(
                f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}",
                timeout=4
            ).json()
            if prof and isinstance(prof, list):
                name = prof[0].get("companyName", ticker)
        except Exception:
            pass

        return {
            "Ticker":      ticker,
            "Empresa":     name,
            "Precio":      precio,
            "Target Med.": median_t,
            "Upside %":    upside,
            "# Analistas": len(targets),
        }
    except Exception:
        return None


def _get_analyst_data_yahoo(ticker: str) -> dict | None:
    """Fallback con Yahoo Finance."""
    try:
        info = yf.Ticker(ticker).info or {}
        cur  = info.get("currentPrice") or info.get("regularMarketPrice")
        tar  = info.get("targetMedianPrice")
        n    = info.get("numberOfAnalystOpinions")
        if not cur or not tar or cur == 0:
            return None
        upside = round(((tar / cur) - 1) * 100, 2)
        if upside <= 0:
            return None
        return {
            "Ticker":      ticker,
            "Empresa":     info.get("shortName", ticker),
            "Precio":      cur,
            "Target Med.": tar,
            "Upside %":    upside,
            "# Analistas": n if n else "N/D",
        }
    except Exception:
        return None


# ── UI ───────────────────────────────────────────────────────────────────────
def render_tab_analistas():
    st.markdown('<p class="section-header">📈 Recomendaciones de Wall Street</p>',
                unsafe_allow_html=True)
    st.caption(
        "Ranking por **Upside %** — potencial de suba según el Target Price mediano "
        "de los analistas de Wall Street. Datos vía FMP + Yahoo Finance como respaldo."
    )

    fmp_key = _fmp_key()

    # ── Controles ────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        n_scan = st.slider(
            "📊 Empresas a escanear",
            min_value=20, max_value=300, value=100, step=10,
            help="FMP: ~0.2s/empresa. Yahoo (respaldo): ~0.6s/empresa."
        )
    with col2:
        usar_cache = st.toggle(
            "💾 Usar caché local (más rápido)",
            value=True,
            help="Si está activo, usa datos en caché de búsquedas anteriores sin consumir API."
        )
    with col3:
        min_upside = st.number_input("📌 Upside mín. %", min_value=0, max_value=100, value=5, step=5)

    fuente = "FMP" if fmp_key else "Yahoo Finance (FMP no configurado)"
    st.caption(f"🔌 Fuente activa: **{fuente}**")

    if not fmp_key:
        st.warning(
            "⚠️ FMP Key no configurada. Se usará Yahoo Finance como respaldo "
            "(más lento y con rate-limit). "
            "Configurá `FMP_KEY` en `.streamlit/secrets.toml` para mejores resultados."
        )

    # ── Escaneo ──────────────────────────────────────────
    if st.button("🔍 Escanear Consenso de Analistas", use_container_width=True, type="primary"):
        tickers    = get_sp500_tickers()[:n_scan]
        resultados = []
        desde_cache = 0

        prog   = st.progress(0)
        status = st.empty()

        for i, t in enumerate(tickers):
            status.text(f"[{i+1}/{len(tickers)}] Consultando {t}...")

            # 1. Intentar caché local
            if usar_cache:
                c = get_cached(f"analyst_{t}")
                if c:
                    if c.get("Upside %", 0) >= min_upside:
                        resultados.append(c)
                    desde_cache += 1
                    prog.progress((i + 1) / len(tickers))
                    continue

            # 2. FMP (preferido)
            dato = None
            if fmp_key:
                dato = _get_analyst_data_fmp(t, fmp_key)
                time.sleep(0.18)
            else:
                dato = _get_analyst_data_yahoo(t)
                time.sleep(0.55)

            if dato:
                set_cache(f"analyst_{t}", dato)
                if dato.get("Upside %", 0) >= min_upside:
                    resultados.append(dato)

            prog.progress((i + 1) / len(tickers))

        status.empty()

        # ── Resultados ────────────────────────────────────
        if resultados:
            df = (
                pd.DataFrame(resultados)
                .sort_values("Upside %", ascending=False)
                .head(10)
                .reset_index(drop=True)
            )
            df.index += 1

            # Formato visual
            df_disp = df.copy()
            df_disp["Precio"]      = df_disp["Precio"].apply(lambda x: f"USD {float(x):,.2f}")
            df_disp["Target Med."] = df_disp["Target Med."].apply(lambda x: f"USD {float(x):,.2f}")
            df_disp["Upside %"]    = df_disp["Upside %"].apply(lambda x: f"🟢 +{float(x):.2f}%")

            st.subheader(f"🏆 Top 10 con mayor potencial de suba")
            st.dataframe(df_disp, use_container_width=True, hide_index=False)

            # Métricas resumen
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("✅ Con upside positivo", f"{len(resultados)} / {len(tickers)}")
            col_b.metric("🎯 Mayor Upside", df_disp["Upside %"].iloc[0])
            col_c.metric("💾 Desde caché", f"{desde_cache} tickers")

            st.balloons()

        else:
            st.warning(
                f"No se encontraron empresas con Upside ≥ {min_upside}% en la muestra. "
                "Probá reducir el Upside mínimo o ampliar la cantidad de empresas."
            )