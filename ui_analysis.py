# ui_analysis.py
import streamlit as st
import pandas as pd
from logic_data import fetch_batch_data
from logic_finance import calcular_rsi, evaluar_multifactor


def render_tab_analysis():
    st.header("🎯 Análisis de Mi Cartera Personal")
    st.caption("Evaluación técnica individual de tus activos (RSI + SMA 50).")

    if "mi_portfolio" not in st.session_state or st.session_state.mi_portfolio.empty:
        st.warning("Cargá activos en la pestaña **Portafolio** primero.")
        return

    if st.button("🔎 Analizar mi Cartera", use_container_width=True):
        my_ticks = [
            str(t).split(".")[0].upper().strip()
            for t in st.session_state.mi_portfolio["Ticker"].tolist()
            if str(t).strip().upper() not in ["", "NONE", "NAN"]
        ]

        if not my_ticks:
            st.error("No hay tickers válidos para analizar.")
            return

        with st.spinner("Descargando datos y calculando indicadores..."):
            raw          = fetch_batch_data(my_ticks)
            analysis_res = []

            for t in my_ticks:
                try:
                    # fetch_batch_data siempre devuelve un dict {ticker: DataFrame}
                    # tanto para uno como para múltiples tickers.
                    df_t = raw.get(t)
                    if df_t is None or df_t.empty:
                        analysis_res.append({
                            "Activo": t, "Precio USD": "N/D",
                            "RSI": "N/D", "Estado": "Sin datos", "RECOMENDACIÓN": "⛔ Sin datos"
                        })
                        continue

                    # Extraemos la columna Close (compatible con cualquier versión de yfinance)
                    close = df_t["Close"]
                    if isinstance(close, pd.DataFrame):
                        close = close.iloc[:, 0]
                    close = close.dropna()

                    if len(close) < 15:
                        continue

                    px   = float(close.iloc[-1])
                    rsi  = calcular_rsi(close)
                    sma  = close.rolling(50).mean().iloc[-1]
                    txt, _, score = evaluar_multifactor(rsi, px, sma)

                    if score >= 2:
                        rec = "🔥 COMPRAR / INCREMENTAR"
                    elif score <= -2:
                        rec = "💰 TOMAR GANANCIA"
                    else:
                        rec = "⚖️ MANTENER"

                    analysis_res.append({
                        "Activo":         t,
                        "Precio USD":     f"{px:.2f}",
                        "RSI":            rsi,
                        "SMA 50":         f"{sma:.2f}" if not pd.isna(sma) else "N/D",
                        "Estado":         txt,
                        "RECOMENDACIÓN":  rec,
                    })

                except Exception as e:
                    analysis_res.append({
                        "Activo": t, "Precio USD": "Error",
                        "RSI": "—", "Estado": str(e)[:40], "RECOMENDACIÓN": "⛔ Error"
                    })

        if analysis_res:
            st.subheader("📋 Resultados del Análisis")
            st.dataframe(
                pd.DataFrame(analysis_res),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "🔵 RSI < 35 = sobreventa (posible compra) · "
                "🔴 RSI > 65 = sobrecompra (posible toma de ganancia) · "
                "SMA 50 = tendencia de mediano plazo."
            )
        else:
            st.error("No se pudo procesar ningún activo. Verificá la conexión e intentá de nuevo.")