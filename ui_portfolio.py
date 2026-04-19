# ui_portfolio.py
import streamlit as st
import pandas as pd
import yfinance as yf


def _get_close_price(ticker_ba: str) -> float | None:
    """
    Obtiene el último precio FORZANDO descarga sin caché.
    Compatible con yfinance 0.2.x y 0.2.40+.
    """
    try:
        # CLAVE: auto_adjust=False y period="5d" evita el caché interno de yfinance
        data = yf.download(
            ticker_ba, 
            period="5d", 
            progress=False, 
            auto_adjust=False,
            prepost=False,
            threads=False  # Evita problemas de concurrencia
        )
        
        if data.empty:
            return None

        # Usamos 'Adj Close' en lugar de 'Close' para tener el precio ajustado
        close = data["Adj Close"] if "Adj Close" in data.columns else data["Close"]

        # yfinance moderno devuelve DataFrame con columnas [ticker_ba]
        if isinstance(close, pd.DataFrame):
            col = ticker_ba if ticker_ba in close.columns else close.columns[0]
            serie = close[col].dropna()
        else:
            # yfinance clásico devuelve Serie directamente
            serie = close.dropna()

        return float(serie.iloc[-1]) if not serie.empty else None

    except Exception:
        return None


def render_tab_portfolio():
    st.header("💼 Mis CEDEARs y ETFs (BYMA)")

    # --- 1. EDITOR DE CARTERA ---
    edited_df = st.data_editor(
        st.session_state.mi_portfolio,
        num_rows="dynamic",
        width="stretch",  # Corregido: era use_container_width=True
        key="portfolio_editor_final",
        column_config={
            "Ticker":    st.column_config.TextColumn("Ticker", help="Ej: AAPL, NVDA, MELI"),
            "Cant":      st.column_config.NumberColumn("Cantidad", min_value=0, format="%.2f"),
            "Costo ARS": st.column_config.NumberColumn("Costo Total ARS", min_value=0, format="$ %,.2f"),
        }
    )

    # --- 2. GUARDAR CAMBIOS ---
    if st.button("💾 Guardar Cambios"):
        cleaned = edited_df.dropna(subset=["Ticker"]).copy()
        cleaned = cleaned[
            ~cleaned["Ticker"].astype(str).str.strip().str.upper().isin(["", "NONE", "NAN"])
        ]
        st.session_state.mi_portfolio = cleaned.reset_index(drop=True)
        st.session_state.mi_portfolio.to_csv("portfolio.csv", index=False)
        st.success("✅ Cambios guardados correctamente.")
        st.rerun()

    st.divider()

    # --- 3. CALCULAR GANANCIAS (SIN CACHÉ) ---
    if st.button("💰 Calcular Ganancias Reales (ARS)", use_container_width=True):
        df = st.session_state.mi_portfolio
        if df.empty:
            st.warning("Agregá activos y guardá primero.")
            return

        res_list  = []
        errores   = []
        progreso  = st.progress(0)
        status    = st.empty()
        total_inv = 0.0
        total_val = 0.0

        with st.spinner("Obteniendo cotizaciones en vivo de BYMA..."):
            filas_validas = df[
                ~df["Ticker"].astype(str).str.strip().str.upper().isin(["", "NONE", "NAN"])
            ]

            for i, (_, row) in enumerate(filas_validas.iterrows()):
                ticker     = str(row.get("Ticker", "")).upper().strip()
                ticker_ba  = f"{ticker}.BA"
                status.text(f"Consultando {ticker_ba}...")

                # SIEMPRE descarga sin caché
                precio_hoy = _get_close_price(ticker_ba)

                if precio_hoy is not None:
                    try:
                        cant        = float(row.get("Cant", 0))
                        costo_total = float(row.get("Costo ARS", 0))
                        val_hoy     = cant * precio_hoy
                        ganancia    = val_hoy - costo_total
                        porc        = (ganancia / costo_total * 100) if costo_total > 0 else 0.0

                        total_inv += costo_total
                        total_val += val_hoy

                        # Color de rendimiento
                        emoji = "🟢" if porc >= 0 else "🔴"

                        res_list.append({
                            "Ticker":     ticker,
                            "Precio Hoy": f"$ {precio_hoy:,.2f}",
                            "Invertiste": f"$ {costo_total:,.2f}",
                            "Vale Hoy":   f"$ {val_hoy:,.2f}",
                            "Rinde %":    f"{emoji} {porc:+.2f}%",
                        })
                    except (ValueError, TypeError):
                        errores.append(f"{ticker}: datos inválidos (revisá Cant o Costo)")
                else:
                    errores.append(f"{ticker}: no se encontró cotización en BYMA")

                progreso.progress((i + 1) / len(filas_validas))

        status.empty()

        # --- RESULTADOS ---
        if res_list:
            st.subheader("📊 Detalle por Activo")
            st.table(pd.DataFrame(res_list))

            # Resumen total
            ganancia_total = total_val - total_inv
            pct_total      = (ganancia_total / total_inv * 100) if total_inv > 0 else 0.0
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("💵 Total Invertido",  f"$ {total_inv:,.2f}")
            col2.metric("📈 Valor Actual",     f"$ {total_val:,.2f}")
            col3.metric("📊 Rendimiento Total",f"{pct_total:+.2f}%", delta=f"$ {ganancia_total:+,.2f}")

        if errores:
            with st.expander(f"⚠️ {len(errores)} activo(s) no consultados"):
                for e in errores:
                    st.caption(e)

        if not res_list:
            st.error(
                "No se pudo obtener ningún precio. "
                "Yahoo Finance puede estar saturado; reintentá en 1 minuto."
            )