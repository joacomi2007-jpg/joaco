# ui_fundamental.py
import streamlit as st
from logic_data import fetch_fundamental_data
from logic_ia import analizar_fundamental_ia
from logic_external import get_external_links
from cache_manager import get_cache_info, list_cached_tickers
from styles import badge, veredicto_badge

# ── Helpers de formato ──────────────────────────────────────────────────────
def _f(val, suffix="", prefix="", na="N/A"):
    if val in ("N/A", None, 0, 0.0, ""):
        return na
    try:
        v = float(val)
        if abs(v) >= 1_000_000_000:
            return f"{prefix}{v/1_000_000_000:.2f}B"
        if abs(v) >= 1_000_000:
            return f"{prefix}{v/1_000_000:.1f}M"
        return f"{prefix}{v:,.2f}{suffix}"
    except Exception:
        return str(val)

def _color_metric(val, good_dir="high", low_ok=None, high_ok=None):
    """Retorna (value_str, delta_str, delta_color) para st.metric."""
    if val in ("N/A", None, 0, 0.0):
        return "N/A", None, None
    try:
        v = float(val)
        if good_dir == "high":
            delta = "▲ Alto" if (high_ok is None or v >= high_ok) else ("▼ Bajo" if low_ok and v < low_ok else None)
        else:
            delta = "▼ Bajo" if (low_ok is None or v <= low_ok) else ("▲ Alto" if high_ok and v > high_ok else None)
        return str(round(v, 2)), delta, "normal"
    except Exception:
        return str(val), None, None


# ── UI Principal ────────────────────────────────────────────────────────────
def render_tab_fundamental():
    st.markdown('<p class="section-header">🏛️ Análisis Fundamental</p>', unsafe_allow_html=True)

    # ── Selector de ticker ─────────────────────────────
    col_in, col_sel, col_btn = st.columns([2, 2, 1])
    with col_in:
        t_man = st.text_input("✍️ Ticker (ej: AAPL, NU, AVGO)", key="fund_ticker_input").upper().strip()
    with col_sel:
        popular = ["", "AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "AMZN",
                   "BRK-B", "LLY", "JPM", "V", "UNH", "XOM", "AVGO", "NU"]
        t_sel = st.selectbox("⭐ Acciones populares", options=popular, key="fund_ticker_sel")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        force = st.toggle("🔄 Forzar actualización", value=False, key="fund_force")

    ticker_final = t_man if t_man else t_sel
    if not ticker_final:
        # Mostrar tickers en caché
        cached_list = list_cached_tickers()
        if cached_list:
            st.caption(f"💾 Tickers en caché local: {', '.join(sorted(cached_list)[:20])}")
        st.info("Ingresá un ticker para comenzar el análisis.")
        return

    # ── Info de caché ─────────────────────────────────
    ci = get_cache_info(ticker_final)
    st.caption(f"📦 Caché: {ci['cached_at_str']}")

# 1. El botón principal ahora solo guarda qué ticker queremos ver
    if st.button(f"📊 Analizar {ticker_final}", use_container_width=True, type="primary"):
        st.session_state["ticker_activo_fund"] = ticker_final

    # 2. Si la app recuerda que estamos analizando este ticker, muestra todo
    if st.session_state.get("ticker_activo_fund") == ticker_final:

        with st.spinner(f"Consolidando datos de múltiples fuentes para **{ticker_final}**..."):
            d = fetch_fundamental_data(ticker_final, force_refresh=force)

        if not d:
            st.error(f"No se encontraron datos para **{ticker_final}**. Verificá el ticker.")
            return

        # Advertencia de datos viejos
        if d.get("_stale"):
            st.markdown(
                '<div class="stale-warning">⚠️ Mostrando datos del caché anterior '
                '(todas las APIs fallaron). Los datos pueden estar desactualizados.</div>',
                unsafe_allow_html=True
            )

        # Fuentes usadas
        sources_html = "".join([badge(s) for s in d.get("_source", [])])
        st.markdown(f"**Fuentes:** {sources_html}", unsafe_allow_html=True)

        # ── CABECERA ──────────────────────────────────
        st.markdown(f"## {d.get('nombre', ticker_final)}")
        st.caption(f"📂 {d.get('sector','N/A')}  ›  {d.get('industria','N/A')}")

        if d.get("descripcion") not in ("N/A", None):
            with st.expander("📝 Descripción del negocio"):
                st.write(d["descripcion"])

        # Precio destacado + 52W
        pc1, pc2, pc3, pc4 = st.columns(4)
        precio_str = f"USD {d['precio']:.2f}" if d.get("precio",0) > 0 else "N/D"
        pc1.metric("💲 Precio Actual", precio_str)
        pc2.metric("📐 Beta",         _f(d.get("beta")))
        pc3.metric("📈 52W Máx",      f"USD {_f(d.get('semana52_max'))}")
        pc4.metric("📉 52W Mín",      f"USD {_f(d.get('semana52_min'))}")

        st.markdown("---")

        # ── TABS INTERNOS ─────────────────────────────
        t_val, t_rent, t_crec, t_salud, t_analistas, t_ia = st.tabs([
            "📐 Valuación", "💰 Rentabilidad", "🚀 Crecimiento",
            "🏦 Salud Financiera", "🎯 Analistas", "🤖 IA"
        ])

        # ─ 1. VALUACIÓN ──────────────────────────────
        with t_val:
            st.markdown('<p class="section-header">Métricas de Valuación</p>', unsafe_allow_html=True)
            v1, v2, v3 = st.columns(3)
            v1.metric("P/E Trailing",   _f(d.get("pe"),  "x"))
            v2.metric("P/E Forward",    _f(d.get("fwd_pe"), "x"))
            v3.metric("PEG Ratio",      _f(d.get("peg")))

            v4, v5, v6 = st.columns(3)
            v4.metric("Price/Book",     _f(d.get("pb"),  "x"))
            v5.metric("Price/Sales",    _f(d.get("ps"),  "x"))
            v6.metric("EV/EBITDA",      _f(d.get("ev_ebitda"), "x"))

            v7, v8 = st.columns(2)
            v7.metric("Market Cap",     _f(d.get("mcap"),    prefix="$ "))
            v8.metric("Enterprise Value",_f(d.get("ev"),     prefix="$ "))

            # Semáforo rápido
            _show_valuation_gauge(d)

        # ─ 2. RENTABILIDAD ───────────────────────────
        with t_rent:
            st.markdown('<p class="section-header">Márgenes y Retornos</p>', unsafe_allow_html=True)
            r1, r2, r3 = st.columns(3)
            r1.metric("ROE",             _f(d.get("roe"),         "%"))
            r2.metric("ROA",             _f(d.get("roa"),         "%"))
            r3.metric("Margen Bruto",    _f(d.get("margen_bruto"),"%"))

            r4, r5, r6 = st.columns(3)
            r4.metric("Margen Operativo",_f(d.get("margen_op"),   "%"))
            r5.metric("Margen Neto",     _f(d.get("margen_neto"), "%"))
            r6.metric("EBITDA",          _f(d.get("ebitda"), prefix="$ "))

            r7, r8 = st.columns(2)
            r7.metric("Div. Yield",      _f(d.get("div_yield"),   "%"))
            r8.metric("Payout Ratio",    _f(d.get("payout_ratio"),"%"))

        # ─ 3. CRECIMIENTO ────────────────────────────
        with t_crec:
            st.markdown('<p class="section-header">Tasas de Crecimiento (YoY)</p>', unsafe_allow_html=True)
            g1, g2 = st.columns(2)
            rg = d.get("revenue_growth","N/A")
            eg = d.get("earnings_growth","N/A")
            g1.metric("Revenue Growth",  _f(rg, "%"),
                      delta="Positivo" if _v_num(rg, 0) else ("Negativo" if _v_num(rg) else None))
            g2.metric("Earnings Growth", _f(eg, "%"),
                      delta="Positivo" if _v_num(eg, 0) else ("Negativo" if _v_num(eg) else None))

        # ─ 4. SALUD FINANCIERA ───────────────────────
        with t_salud:
            st.markdown('<p class="section-header">Balance y Liquidez</p>', unsafe_allow_html=True)
            s1, s2, s3 = st.columns(3)
            s1.metric("Current Ratio",  _f(d.get("current_ratio")))
            s2.metric("Quick Ratio",    _f(d.get("quick_ratio")))
            s3.metric("Deuda / Equity", _f(d.get("deuda_eq")))

            s4, s5, s6 = st.columns(3)
            s4.metric("Deuda Total",    _f(d.get("deuda_total"), prefix="$ "))
            s5.metric("Cash",           _f(d.get("cash"),        prefix="$ "))
            s6.metric("Free Cash Flow", _f(d.get("fcf"),         prefix="$ "))

        # ─ 5. ANALISTAS ──────────────────────────────
        with t_analistas:
            st.markdown('<p class="section-header">Consenso de Mercado</p>', unsafe_allow_html=True)
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Target Price",   f"USD {_f(d.get('target_price'))}")
            a2.metric("Upside %",       _f(d.get("upside_pct"), "%"))
            a3.metric("Recomendación",  str(d.get("recomendacion","N/A")))
            a4.metric("# Analistas",    str(d.get("n_analistas","N/A")))

            # Links externos
            st.markdown('<p class="section-header" style="margin-top:16px">🔗 Consultas Externas</p>',
                        unsafe_allow_html=True)
            links = get_external_links(ticker_final)
            l1, l2, l3, l4 = st.columns(4)
            l1.link_button("📈 Yahoo Finance", links["Yahoo Finance"], use_container_width=True)
            l2.link_button("📊 Finviz",        links["Finviz"],        use_container_width=True)
            l3.link_button("🌎 Investing",      links["Investing"],     use_container_width=True)
            l4.link_button("📉 TradingView",    links["TradingView"],   use_container_width=True)

# ─ 6. ANÁLISIS IA ────────────────────────────
        with t_ia:
            st.markdown('<p class="section-header">🤖 Análisis IA (Llama 3.3)</p>', unsafe_allow_html=True)
            st.caption("La IA recibe TODOS los datos fundamentales y entrega un veredicto de inversión.")

            # 1. Creamos una llave única para la memoria de ESTE ticker
            state_key = f"ia_result_{ticker_final}"

            # 2. El botón ahora SOLO guarda el resultado en st.session_state
            if st.button("🧠 Generar Análisis IA", use_container_width=True, type="primary",
                         key=f"btn_generar_ia_{ticker_final}"):
                with st.spinner("Analizando datos fundamentales con IA..."):
                    # Guardamos el resultado de Groq directamente en la memoria
                    st.session_state[state_key] = analizar_fundamental_ia(ticker_final, d)

            # 3. Fuera del botón, revisamos si la memoria ya tiene el análisis de este ticker
            if state_key in st.session_state:
                ia = st.session_state[state_key] # Recuperamos los datos
                
                if ia.get("error"):
                    st.error(f"Error en IA: {ia['error']}")
                else:
                    # Mostramos el resultado que estaba guardado
                    _render_ia_result(ia, ticker_final)


# ── Renders auxiliares ──────────────────────────────────────────────────────
def _v_num(val, threshold=None) -> bool:
    try:
        v = float(val)
        return v > threshold if threshold is not None else True
    except Exception:
        return False


def _show_valuation_gauge(d: dict):
    """Muestra un semáforo de valuación simple."""
    pe  = d.get("pe")
    peg = d.get("peg")
    pb  = d.get("pb")

    señales = []
    try:
        if float(pe) < 15:    señales.append("🟢 P/E bajo (posible infravaloración)")
        elif float(pe) > 30:  señales.append("🔴 P/E elevado (mercado paga prima)")
        else:                  señales.append("🟡 P/E moderado")
    except Exception: pass

    try:
        if float(peg) < 1:    señales.append("🟢 PEG < 1 (crecimiento no está descontado)")
        elif float(peg) > 2:  señales.append("🔴 PEG > 2 (crecimiento caro)")
    except Exception: pass

    try:
        if float(pb) < 1:     señales.append("🟢 P/B < 1 (cotiza bajo valor libro)")
        elif float(pb) > 5:   señales.append("🟠 P/B alto")
    except Exception: pass

    if señales:
        with st.expander("📊 Semáforo de valuación rápida"):
            for s in señales:
                st.markdown(f"- {s}")


def _render_ia_result(ia: dict, ticker: str):
    v = ia.get("veredicto", "N/A").upper()
    col_v, col_p = st.columns([3, 1])
    with col_v:
        st.markdown(
            f'<div class="ia-card">'
            f'<h3>Veredicto para {ticker}</h3>'
            f'{veredicto_badge(v)}'
            f'</div>',
            unsafe_allow_html=True
        )
    with col_p:
        score = ia.get("puntuacion", "N/A")
        st.markdown(
            f'<div class="ia-card" style="text-align:center">'
            f'<h3>Puntuación</h3>'
            f'<span style="font-size:2rem;font-weight:800;color:#4f8ef7">{score}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ✅ Fortalezas")
        for f in ia.get("fortalezas","N/A").split(" | "):
            st.markdown(f"- {f.strip()}")
    with c2:
        st.markdown("#### ⚠️ Riesgos")
        for r in ia.get("riesgos","N/A").split(" | "):
            st.markdown(f"- {r.strip()}")

    st.markdown("#### 📋 Análisis")
    st.info(ia.get("analisis","N/A"))
    st.markdown("#### 🎯 Conclusión")
    st.success(ia.get("conclusion","N/A"))