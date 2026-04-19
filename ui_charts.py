# ui_charts.py
from logic_ia import analizar_datos_groq, analizar_grafico_gemini
"""
Pestaña de Gráficos con TradingView Advanced Chart Widget.
Incluye: cambio de periodo, herramientas de dibujo, Fibonacci, SMAs, indicadores.
"""
import streamlit as st

# Prefijos de exchange más comunes
EXCHANGE_MAP = {
    "AAPL": "NASDAQ", "MSFT": "NASDAQ", "GOOGL": "NASDAQ", "GOOG": "NASDAQ",
    "AMZN": "NASDAQ", "META": "NASDAQ", "NVDA": "NASDAQ", "TSLA": "NASDAQ",
    "AVGO": "NASDAQ", "INTC": "NASDAQ", "AMD": "NASDAQ", "QCOM": "NASDAQ",
    "CSCO": "NASDAQ", "NFLX": "NASDAQ", "ADBE": "NASDAQ", "INTU": "NASDAQ",
    "PYPL": "NASDAQ", "SBUX": "NASDAQ", "GILD": "NASDAQ", "AMGN": "NASDAQ",
    "JPM": "NYSE",  "V": "NYSE",    "JNJ": "NYSE",  "WMT": "NYSE",
    "MA": "NYSE",   "PG": "NYSE",   "HD": "NYSE",   "CVX": "NYSE",
    "BAC": "NYSE",  "KO": "NYSE",   "PFE": "NYSE",  "DIS": "NYSE",
    "MCD": "NYSE",  "GS": "NYSE",   "BRK-B": "NYSE","XOM": "NYSE",
    "UNH": "NYSE",  "LLY": "NYSE",  "TMO": "NYSE",  "ABT": "NYSE",
    "MELI": "NASDAQ", "NU": "NYSE", "DESP": "NYSE", "LOMA": "NYSE", "GGAL": "NYSE",
}

INTERVALS = {
    "1 minuto":    "1",
    "5 minutos":   "5",
    "15 minutos":  "15",
    "30 minutos":  "30",
    "1 hora":      "60",
    "4 horas":     "240",
    "Diario":      "D",
    "Semanal":     "W",
    "Mensual":     "M",
}

THEMES = {"Oscuro": "dark", "Claro": "light"}


def _tradingview_html(symbol: str, interval: str, theme: str, height: int) -> str:
    """Genera el HTML del widget TradingView Advanced Chart."""
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body, html {{
      margin: 0; padding: 0;
      background: {'#0f1117' if theme == 'dark' else '#ffffff'};
    }}
    #tv_chart_container {{
      width: 100%;
      height: {height}px;
    }}
  </style>
</head>
<body>
  <div id="tv_chart_container"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
    new TradingView.widget({{
      "container_id":       "tv_chart_container",
      "autosize":           true,
      "symbol":             "{symbol}",
      "interval":           "{interval}",
      "timezone":           "America/New_York",
      "theme":              "{theme}",
      "style":              "1",
      "locale":             "es",
      "toolbar_bg":         "{'#161b27' if theme == 'dark' else '#f8f9fa'}",
      "enable_publishing":  false,
      "withdateranges":     true,
      "hide_side_toolbar":  false,
      "allow_symbol_change": true,
      "save_image":         true,
      "calendar":           false,
      "hotlist":            true,
      "details":            true,
      "studies": [
        "STD;RSI",
        "STD;MACD",
        "STD;Bollinger_Bands",
        "STD;Volume"
      ],
      "show_popup_button":  true,
      "popup_width":        "1000",
      "popup_height":       "650"
    }});
  </script>
</body>
</html>
"""


def render_tab_charts():
    st.markdown('<p class="section-header">📉 Gráfico Avanzado (TradingView)</p>',
                unsafe_allow_html=True)
    st.caption(
        "Gráfico interactivo con herramientas de dibujo, Fibonacci, SMAs y más. "
        "Podés trazar líneas, canales y figuras directamente en el gráfico."
    )

    # Inicializar session_state para el ticker si no existe
    if "chart_ticker_value" not in st.session_state:
        st.session_state.chart_ticker_value = "AAPL"

    # ── Controles ──────────────────────────────────────
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1:
        ticker_input = st.text_input(
            "🔍 Ticker",
            value=st.session_state.chart_ticker_value,
            key="chart_ticker",
            placeholder="Ej: AAPL, MSFT, NVDA, SPY, QQQ"
        ).upper().strip()
# --- TRADUCTOR Y LIMPIEZA (Único bloque necesario) ---
    ticker_para_groq = ticker_input.replace(".", "-")
    if ticker_para_groq == "BRKB": ticker_para_groq = "BRK-B"
    
    ticker_para_grafico = ticker_input.replace("-", ".")
    if ticker_para_grafico == "BRKB": ticker_para_grafico = "BRK.B"

    # Inicializar y resetear si cambia el ticker
    if "ticker_rastreo" not in st.session_state:
        st.session_state.ticker_rastreo = ticker_para_groq

    if ticker_para_groq != st.session_state.ticker_rastreo:
        st.session_state.analisis_memoria = "" # Limpia el informe viejo
        st.session_state.ticker_rastreo = ticker_para_groq
    with col2:
        interval_label = st.selectbox(
            "⏱️ Período",
            options=list(INTERVALS.keys()),
            index=6,   # "Diario" por defecto
            key="chart_interval"
        )

    with col3:
        theme_label = st.selectbox(
            "🎨 Tema",
            options=list(THEMES.keys()),
            index=0,
            key="chart_theme"
        )

    with col4:
        height = st.selectbox(
            "📐 Alto",
            options=[500, 600, 700, 800],
            index=1,
            key="chart_height"
        )

# ── Construir símbolo con exchange ──────────────────
    # Usamos ticker_para_groq (con guion) para el MAPA
   # Usamos ticker_para_groq para el MAPA, pero ticker_para_grafico para las VELAS
    exchange = EXCHANGE_MAP.get(ticker_para_groq, "")
    symbol = f"{exchange}:{ticker_para_grafico}" if exchange else ticker_para_grafico
    interval = INTERVALS[interval_label]
    theme = THEMES[theme_label]
    # ── Info de indicadores disponibles ─────────────────
    with st.expander("📌 Cómo usar el gráfico — Herramientas disponibles"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("""
**📏 Herramientas de Dibujo** (barra lateral derecha)
- Líneas de tendencia
- Canales horizontales y diagonales
- Rectángulos y flechas
- Texto y etiquetas
""")
        with col_b:
            st.markdown("""
**📐 Fibonacci** (menú de herramientas)
- Retroceso de Fibonacci
- Extensiones de Fibonacci
- Abanicos de Fibonacci
- Círculos de Fibonacci
""")
        with col_c:
            st.markdown("""
**📊 Indicadores incluidos**
- RSI (14)
- MACD
- Bollinger Bands
- Volumen
- Agregar más: botón "Indicadores" ↑
""")

    st.caption(f"📡 Mostrando: **{symbol}** · Período: **{interval_label}**")

    # ── Renderizar widget ────────────────────────────────
    html_code = _tradingview_html(symbol, interval, theme, height)
    st.iframe(html_code, height=height + 20)

    # ── Accesos rápidos a otros tickers ─────────────────
    st.markdown("---")
    st.markdown("**⭐ Acceso Rápido**")

    quick_tickers = [
        "AAPL", "MSFT", "NVDA", "TSLA", "META",
        "GOOGL", "AMZN", "SPY", "QQQ", "BRK-B",
        "MELI", "NU", "DESP", "LOMA", "GGAL",
    ]

    cols = st.columns(len(quick_tickers))
    for i, qt in enumerate(quick_tickers):
        if cols[i].button(qt, key=f"quick_{qt}", use_container_width=True):
            st.session_state.chart_ticker_value = qt
            st.rerun()
# ── Sección de Análisis por Datos (Groq) ────────────────
    st.markdown("---")
    
    # Lógica para resetear la memoria si el ticker cambia
    if "ticker_rastreo" not in st.session_state:
        st.session_state.ticker_rastreo = ticker_input

    if ticker_input != st.session_state.ticker_rastreo:
        st.session_state.analisis_memoria = ""  # Limpiamos el análisis viejo
        st.session_state.ticker_rastreo = ticker_input

    # 1. Inicializamos la memoria si no existe
    if "analisis_memoria" not in st.session_state:
        st.session_state.analisis_memoria = ""

    # 2. Botón de disparo
    if st.button("🔍 Ejecutar Análisis de Indicadores", type="secondary", use_container_width=True):
        if not ticker_input:
            st.error("⚠️ Por favor, ingresá un ticker válido primero.")
        else:
            with st.spinner(f"Consultando indicadores técnicos para {ticker_input}..."):
                st.session_state.analisis_memoria = analizar_datos_groq(ticker_para_groq)

# 3. Mostramos el resultado (Asegurate de que esté indentado dentro de la función)
    if st.session_state.analisis_memoria:
        with st.chat_message("assistant", avatar="📊"):
            # 1. Limpiamos las etiquetas del texto para que el informe se vea profesional
            texto_limpio = st.session_state.analisis_memoria \
                .replace("[VEREDICTO: COMPRA]", "") \
                .replace("[VEREDICTO: ESPERAR]", "") \
                .replace("[VEREDICTO: VENTA]", "")
            
            st.markdown(f"### 📋 Informe Técnico: **{ticker_para_groq}**")
            st.markdown(texto_limpio)
            
            st.divider() # Una línea para separar el informe del cartel final

            # 2. Lógica de Carteles por Color
            if "[VEREDICTO: COMPRA]" in st.session_state.analisis_memoria:
                st.success(f"🚀 **OPORTUNIDAD DETECTADA:** El análisis técnico sugiere entrada en {ticker_para_groq}.")
            
            elif "[VEREDICTO: VENTA]" in st.session_state.analisis_memoria:
                st.error(f"⚠️ **ALERTA DE VENTA:** Los indicadores sugieren salida o toma de ganancias en {ticker_para_groq}.")
            
            elif "[VEREDICTO: ESPERAR]" in st.session_state.analisis_memoria:
                st.warning(f"⏳ **MODO CAUTELA:** No es momento ideal. Mejor esperar a que {ticker_para_groq} busque soportes.")
            
            else:
                # Si la IA se olvida de la etiqueta, ponemos un aviso neutro
                st.info("ℹ️ Análisis completado. Revisá los niveles de RSI y SMA mencionados arriba.")
    # ── Sección de IA Visual ─────────────────────────────
    st.divider()
    st.markdown("### 🔭 Analista Visual (Gemini)")

    archivo_foto = st.file_uploader("Pegar o subir captura del gráfico", type=["png", "jpg", "jpeg"], key="uploader_gemini")

    if archivo_foto is not None:
        st.image(archivo_foto, caption=f"Gráfico de {ticker_input} listo para analizar", use_container_width=True)
        
        if st.button("🚀 Analizar Proyección 1-3 Años", type="primary", use_container_width=True):
            with st.spinner("Gemini está estudiando las velas y tendencias..."):
                informe_visual = analizar_grafico_gemini(archivo_foto, ticker_para_groq) 
                st.info(informe_visual)