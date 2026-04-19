# logic_ia.py
from google import genai
from PIL import Image
import os
import io
import streamlit as st
import yfinance as yf
from groq import Groq
import streamlit as st
from groq import Groq

MAX_HISTORIAL = 10

def _client():
    try:
        key = st.secrets["GROQ_KEY"]
    except Exception:
        key = os.environ.get("GROQ_KEY", "")
    if not key:
        raise ValueError("GROQ_KEY no configurada en .streamlit/secrets.toml")
    return Groq(api_key=key)


# ---------------------------------------------------------------------------
# CHAT GENERAL
# ---------------------------------------------------------------------------
def obtener_respuesta_ia(pregunta_usuario: str, portfolio_df, historial_previo: list) -> str:
    try:
        client = _client()
        ctx = portfolio_df.to_string(index=False) if portfolio_df is not None and not portfolio_df.empty \
              else "El usuario aún no cargó activos."

        mensajes = [{
            "role": "system",
            "content": (
                "Sos un Analista Financiero estricto Senior especializado en mercados de EE.UU., "
                "CEDEARs y ETFs en Argentina. Respondés de forma técnica, concisa y con datos "
                "concretos. Cuando el usuario pregunta sobre su cartera, usás los datos provistos. "
                "Si no tenés certeza de un dato, lo aclarás.\n\n"
                f"Cartera actual del usuario:\n{ctx}"
            )
        }]

        for m in historial_previo[-MAX_HISTORIAL:]:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                mensajes.append({"role": m["role"], "content": m["content"]})
        mensajes.append({"role": "user", "content": pregunta_usuario})

        r = _client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes,
            temperature=0.6,
            max_tokens=1024,
        )
        return r.choices[0].message.content
    except ValueError as e:
        return f"⚙️ Error de configuración: {e}"
    except Exception as e:
        return f"❌ Error en IA: {str(e)}"


# ---------------------------------------------------------------------------
# ANÁLISIS FUNDAMENTAL IA
# ---------------------------------------------------------------------------
def analizar_fundamental_ia(ticker: str, datos: dict) -> dict:
    """
    Envía TODOS los datos fundamentales a la IA y pide un análisis estructurado.

    Returns:
        {
          "veredicto":   "COMPRAR" | "REFORZAR" | "MANTENER" | "REDUCIR" | "VENDER",
          "puntuacion":  "7/10",
          "fortalezas":  "...",
          "riesgos":     "...",
          "analisis":    "...",
          "conclusion":  "...",
          "raw":         "<respuesta completa>",
          "error":       None | "mensaje de error"
        }
    """
    def _fmt(v):
        if v in (None, "N/A", 0, 0.0):
            return "N/D"
        try:
            return f"{float(v):.2f}"
        except Exception:
            return str(v)
    # Construimos el resumen de datos para el prompt
    resumen = f"""
EMPRESA: {datos.get('nombre','N/D')} ({ticker})
Sector: {datos.get('sector','N/D')} | Industria: {datos.get('industria','N/D')}

VALUACIÓN:
  Precio actual:   USD {_fmt(datos.get('precio'))}
  P/E Trailing:    {_fmt(datos.get('pe'))}x
  P/E Forward:     {_fmt(datos.get('fwd_pe'))}x
  PEG Ratio:       {_fmt(datos.get('peg'))}
  P/B:             {_fmt(datos.get('pb'))}x
  P/S:             {_fmt(datos.get('ps'))}x
  EV/EBITDA:       {_fmt(datos.get('ev_ebitda'))}x
  Beta:            {_fmt(datos.get('beta'))}
  Market Cap:      USD {_fmt(datos.get('mcap'))}
  52W Max/Min:     {_fmt(datos.get('semana52_max'))} / {_fmt(datos.get('semana52_min'))}

RENTABILIDAD:
  ROE:             {_fmt(datos.get('roe'))}%
  ROA:             {_fmt(datos.get('roa'))}%
  Margen Bruto:    {_fmt(datos.get('margen_bruto'))}%
  Margen Operativo:{_fmt(datos.get('margen_op'))}%
  Margen Neto:     {_fmt(datos.get('margen_neto'))}%

CRECIMIENTO:
  Revenue YoY:     {_fmt(datos.get('revenue_growth'))}%
  Earnings YoY:    {_fmt(datos.get('earnings_growth'))}%

SALUD FINANCIERA:
  Current Ratio:   {_fmt(datos.get('current_ratio'))}
  Quick Ratio:     {_fmt(datos.get('quick_ratio'))}
  Deuda/Equity:    {_fmt(datos.get('deuda_eq'))}
  FCF:             USD {_fmt(datos.get('fcf'))}
  EBITDA:          USD {_fmt(datos.get('ebitda'))}
  Deuda Total:     USD {_fmt(datos.get('deuda_total'))}
  Cash:            USD {_fmt(datos.get('cash'))}

DIVIDENDO:
  Yield:           {_fmt(datos.get('div_yield'))}%
  Payout Ratio:    {_fmt(datos.get('payout_ratio'))}%

ANALISTAS (consenso de mercado):
  Target Price:    USD {_fmt(datos.get('target_price'))}
  Upside %:        {_fmt(datos.get('upside_pct'))}%
  Recomendación:   {datos.get('recomendacion','N/D')}
  N° Analistas:    {datos.get('n_analistas','N/D')}

Descripción: {datos.get('descripcion','N/D')}
""".strip()

    prompt = f"""Sos un analista estricto. Analizá los siguientes datos fundamentales de {ticker} y respondé EXACTAMENTE en este formato:

{resumen}

---
Respondé solo con este bloque (sin texto adicional):

VEREDICTO: [COMPRAR / REFORZAR / MANTENER / REDUCIR / VENDER]
PUNTUACION: [X/10]
FORTALEZAS: [2-3 puntos fuertes concretos, separados por " | "]
RIESGOS: [2-3 riesgos concretos, separados por " | "]
ANALISIS: [Párrafo de 3-5 oraciones con el análisis técnico-fundamental integrando tu análisis numérico y contrastándolo con el consenso de analistas]
CONCLUSION: [1 oración de cierre con la recomendación final y por qué]
"""

    try:
        client = _client()
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sos un analista financiero GARP altamente objetivo e independiente. "
                        "Tu objetivo es proyectar el potencial de la empresa a MEDIANO PLAZO (1 a 3 años). "
                        "Evaluás el equilibrio exacto entre Valuación, Crecimiento y Salud Financiera. "
                        "DEBES usar toda la escala de PUNTUACION del 1 al 10 aplicando esta lógica estricta:\n"
                        "- 9 o 10: Empresa excepcional. Crecimiento >20%, deuda nula/baja, altos márgenes y múltiplos de valuación baratos o muy razonables.\n"
                        "- 7 u 8 (COMPRAR/REFORZAR): Buena empresa. Alto crecimiento o márgenes altos, pero con una valuación un poco cara (P/E alto). El crecimiento justifica el precio.\n"
                        "- 5 o 6 (MANTENER): Empresa promedio. Crecimiento moderado/bajo, valuación justa, deuda manejable. O gran empresa pero a un precio ya muy inflado.\n"
                        "- 3 o 4 (REDUCIR): Empresa en riesgo. Crecimiento estancado, deuda alta o márgenes muy finos, cotizando a precios caros.\n"
                        "- 1 o 2 (VENDER): Empresa destructora de valor. Márgenes negativos, quema de caja, altísima deuda y valuación desconectada de la realidad.\n\n"
                        "Respondés SOLO en el formato exacto solicitado. "
                        "Contrastá tu visión numérica con el Target Price del mercado en la sección de ANÁLISIS."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        raw = r.choices[0].message.content.strip()
        return _parse_ia_response(raw)
    except ValueError as e:
        return {"veredicto": "ERROR", "error": str(e), "raw": ""}
    except Exception as e:
        return {"veredicto": "ERROR", "error": str(e), "raw": ""}


def _parse_ia_response(raw: str) -> dict:
    """Parsea la respuesta estructurada de la IA."""
    result = {
        "veredicto": "N/A", "puntuacion": "N/A",
        "fortalezas": "N/A", "riesgos": "N/A",
        "analisis": "N/A", "conclusion": "N/A",
        "raw": raw, "error": None
    }
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("VEREDICTO:"):
            result["veredicto"]  = line.split(":", 1)[1].strip()
        elif line.startswith("PUNTUACION:"):
            result["puntuacion"] = line.split(":", 1)[1].strip()
        elif line.startswith("FORTALEZAS:"):
            result["fortalezas"] = line.split(":", 1)[1].strip()
        elif line.startswith("RIESGOS:"):
            result["riesgos"]    = line.split(":", 1)[1].strip()
        elif line.startswith("ANALISIS:"):
            result["analisis"]   = line.split(":", 1)[1].strip()
        elif line.startswith("CONCLUSION:"):
            result["conclusion"] = line.split(":", 1)[1].strip()
    return result
def analizar_grafico_gemini(archivo_imagen, ticker):
    try:
        key = st.secrets["GEMINI_KEY"]
        client = genai.Client(api_key=key)
        
        # Dieta extrema para no gastar cuota
        img = Image.open(archivo_imagen).convert("L")
        img.thumbnail((600, 600))
        
        prompt = f"Análisis técnico breve de {ticker} (1-3 años). Tendencia y zona de compra."

        # Lista de nombres técnicos REALES que Google suele usar
        modelos_posibles = [
            "gemini-1.5-flash-latest", # El nombre más compatible en 2026
            "gemini-1.5-flash", 
            "gemini-1.5-flash-8b", 
            "gemini-2.0-flash" 
        ]
        
        for m_name in modelos_posibles:
            try:
                respuesta = client.models.generate_content(model=m_name, contents=[prompt, img])
                return f"**(Analizado con {m_name})**\n\n{respuesta.text}"
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg:
                    # Si el error es de cuota, probamos el siguiente modelo
                    # a ver si tiene cuota independiente (a veces pasa)
                    continue 
                if "404" in msg:
                    # Si no lo encuentra, saltamos al siguiente
                    continue
                return f"❌ Error en {m_name}: {str(e)}"

        return "⏳ **Cuota agotada en todos los modelos.** Google te pide esperar 60 segundos."

    except Exception as e:
        return f"❌ Error crítico: {str(e)}"
def analizar_datos_groq(ticker):
    try:
        # 1. Obtener datos reales con yfinance
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y") # Bajamos un año de historia
        
        if hist.empty:
            return "❌ No se encontraron datos para este ticker."

        # 2. Cálculos técnicos básicos
        precio_actual = hist['Close'].iloc[-1]
        max_52w = hist['Close'].max()
        min_52w = hist['Close'].min()
        
        # Calcular RSI (simplificado)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # Medias móviles
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]

        # 3. Preparar el mensaje para Groq
        client = Groq(api_key=st.secrets["GROQ_KEY"])
        
        prompt = f"""
        Actúa como un Analista Técnico Senior con amplia experiencia que desarrolla estrategias de inversión y se extiende en su análisis y da su honesta opinión. Analiza los siguientes datos de {ticker}:
        - Precio Actual: {precio_actual:.2f}
        - RSI (14 días): {rsi:.2f}
        - SMA 50: {sma_50:.2f} | SMA 200: {sma_200:.2f}
        - Máximo 52 semanas: {max_52w:.2f} | Mínimo 52 semanas: {min_52w:.2f}

        Tarea:
        1. ¿Está en sobrecompra o sobreventa (RSI)?
        2. ¿La tendencia es alcista o bajista (comparando precio con SMAs)?
        3. Identifica una resistencia y un soporte cercano basándote en los máximos/mínimos.
        4. ¿Tiene impulso (momentum)?
        5. VEREDICTO FINAL: ¿Es buen momento para comprar a mediano plazo?
        6. Justifica tu veredicto con un análisis técnico breve.
        7. Resume tus conclusiones en un párrafo al final del informe.
        Al final de tu informe, debes incluir obligatoriamente una de estas tres etiquetas según tu conclusión:
        [VEREDICTO: COMPRA] (Si el RSI está bajo y hay tendencia alcista).
        [VEREDICTO: VENTA] (Si hay sobrecompra extrema o ruptura de soportes).
        [VEREDICTO: ESPERAR] (Si el precio está en el medio o hay mucha incertidumbre). 
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", # El modelo más potente de Groq
        )
        
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"❌ Error en Groq Analysis: {str(e)}"