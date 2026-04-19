# logic_data.py
"""
Motor de datos fundamentales multi-fuente con caché local.

Orden de prioridad:
  1. Caché local (< 7 días)  → sin costo, instantáneo
  2. Yahoo Finance            → gratis, muchos campos, sujeto a rate-limit
  3. FMP (Financial Modeling Prep) → confiable, 250 calls/día gratis
  4. Alpha Vantage            → rotación de claves, 24 calls/día por clave
  5. Finnhub                  → 60 calls/min gratis
  6. Caché viejo (stale)     → fallback final, muestra advertencia en UI

Si un campo no está en una fuente, se busca en la siguiente.
"""
import os
import time
import requests
import yfinance as yf
import pandas as pd
import streamlit as st

from cache_manager import (
    get_cached, get_stale, set_cache, get_cache_info,
    get_next_av_key, mark_av_key_exhausted, increment_av_calls,
)

# ---------------------------------------------------------------------------
# CLAVES DE API (leídas de secrets.toml, nunca hardcodeadas)
# ---------------------------------------------------------------------------
def _secrets():
    try:
        return {
            "av_keys":     list(st.secrets.get("AV_KEYS",     [])),
            "fmp_key":     str(st.secrets.get("FMP_KEY",      "")),
            "finnhub_key": str(st.secrets.get("FINNHUB_KEY",  "")),
        }
    except Exception:
        return {
            "av_keys":     os.environ.get("AV_KEYS", "").split(","),
            "fmp_key":     os.environ.get("FMP_KEY", ""),
            "finnhub_key": os.environ.get("FINNHUB_KEY", ""),
        }

# ---------------------------------------------------------------------------
# SCHEMA VACÍO — todos los campos que maneja la app
# ---------------------------------------------------------------------------
def _empty_schema(ticker: str) -> dict:
    return {
        # Identificación
        "nombre":     ticker, "sector": "N/A", "industria": "N/A", "descripcion": "N/A",
        # Precio y mercado
        "precio": 0.0, "mcap": "N/A", "ev": "N/A",
        "semana52_max": "N/A", "semana52_min": "N/A",
        "volumen_avg": "N/A", "beta": "N/A",
        # Valuación
        "pe": "N/A", "fwd_pe": "N/A", "peg": "N/A",
        "pb": "N/A", "ps": "N/A", "ev_ebitda": "N/A",
        # Rentabilidad
        "roe": "N/A", "roa": "N/A",
        "margen_bruto": "N/A", "margen_op": "N/A", "margen_neto": "N/A",
        # Crecimiento
        "revenue_growth": "N/A", "earnings_growth": "N/A",
        # Salud financiera
        "current_ratio": "N/A", "quick_ratio": "N/A",
        "deuda_eq": "N/A", "deuda_total": "N/A",
        "cash": "N/A", "fcf": "N/A", "ebitda": "N/A",
        # Dividendo
        "div_yield": "N/A", "payout_ratio": "N/A",
        # Analistas
        "target_price": "N/A", "recomendacion": "N/A",
        "n_analistas": "N/A", "upside_pct": "N/A",
        # Meta
        "_source": [],   # qué fuentes se usaron
        "_stale": False, # si se usó caché vencido
    }

def _v(val) -> bool:
    """True si el valor es usable."""
    if val in (None, "N/A", "None", "nan", "NULL", "", 0, 0.0):
        return False
    try:
        return not (float(val) == 0)
    except (TypeError, ValueError):
        return isinstance(val, str) and len(val.strip()) > 0

def _pct(val, factor=100) -> float | str:
    """Convierte decimal a porcentaje."""
    try:
        v = float(val)
        return round(v * factor, 2) if factor != 1 else round(v, 2)
    except Exception:
        return "N/A"

def _fill(d: dict, key: str, val) -> None:
    """Solo escribe si el campo está vacío Y el valor es válido."""
    if d.get(key) in (None, "N/A", 0, 0.0) and _v(val):
        try:
            d[key] = round(float(val), 4) if key not in ("nombre", "sector", "industria", "descripcion", "recomendacion") else val
        except (TypeError, ValueError):
            d[key] = val


# ---------------------------------------------------------------------------
# FUENTE 1: YAHOO FINANCE
# ---------------------------------------------------------------------------
def _from_yahoo(ticker: str, d: dict) -> bool:
    t_yahoo = ticker.replace(".", "-")
    try:
        stock = yf.Ticker(t_yahoo)
        info  = stock.info or {}
        hist  = stock.history(period="7d")

        if not hist.empty:
            d["precio"] = round(float(hist["Close"].iloc[-1]), 2)

        # Mapeo directo de campos
        direct = {
            "nombre":       ("longName",                  None),
            "sector":       ("sector",                    None),
            "industria":    ("industry",                  None),
            "beta":         ("beta",                      None),
            "mcap":         ("marketCap",                 None),
            "ev":           ("enterpriseValue",           None),
            "pe":           ("trailingPE",                None),
            "fwd_pe":       ("forwardPE",                 None),
            "peg":          ("pegRatio",                  None),
            "pb":           ("priceToBook",               None),
            "ps":           ("priceToSalesTrailing12Months", None),
            "ev_ebitda":    ("enterpriseToEbitda",        None),
            "deuda_eq":     ("debtToEquity",              None),
            "deuda_total":  ("totalDebt",                 None),
            "cash":         ("totalCash",                 None),
            "fcf":          ("freeCashflow",              None),
            "ebitda":       ("ebitda",                    None),
            "current_ratio":("currentRatio",              None),
            "quick_ratio":  ("quickRatio",                None),
            "semana52_max": ("fiftyTwoWeekHigh",          None),
            "semana52_min": ("fiftyTwoWeekLow",           None),
            "volumen_avg":  ("averageVolume",             None),
            "payout_ratio": ("payoutRatio",               None),
            "n_analistas":  ("numberOfAnalystOpinions",   None),
            "target_price": ("targetMedianPrice",         None),
            "recomendacion":("recommendationKey",         None),
        }
        for local_k, (yahoo_k, _) in direct.items():
            val = info.get(yahoo_k)
            if _v(val):
                _fill(d, local_k, str(val) if local_k in ("nombre","sector","industria","recomendacion") else val)

        # Campos que vienen en decimales
        if _v(info.get("returnOnEquity")):
            _fill(d, "roe",            _pct(info["returnOnEquity"]))
        if _v(info.get("returnOnAssets")):
            _fill(d, "roa",            _pct(info["returnOnAssets"]))
        if _v(info.get("grossMargins")):
            _fill(d, "margen_bruto",   _pct(info["grossMargins"]))
        if _v(info.get("operatingMargins")):
            _fill(d, "margen_op",      _pct(info["operatingMargins"]))
        if _v(info.get("profitMargins")):
            _fill(d, "margen_neto",    _pct(info["profitMargins"]))
        if _v(info.get("dividendYield")):
            _fill(d, "div_yield",      _pct(info["dividendYield"]))
        if _v(info.get("revenueGrowth")):
            _fill(d, "revenue_growth", _pct(info["revenueGrowth"]))
        if _v(info.get("earningsGrowth")):
            _fill(d, "earnings_growth",_pct(info["earningsGrowth"]))
        if _v(info.get("longBusinessSummary")):
            _fill(d, "descripcion",    info["longBusinessSummary"][:400] + "...")

        # Upside si tenemos precio y target
        if _v(d.get("precio")) and _v(d.get("target_price")):
            try:
                up = ((float(d["target_price"]) / float(d["precio"])) - 1) * 100
                _fill(d, "upside_pct", round(up, 2))
            except Exception:
                pass

        if _v(d.get("recomendacion")) and isinstance(d["recomendacion"], str):
            d["recomendacion"] = d["recomendacion"].upper().replace("_", " ")

        d["_source"].append("Yahoo")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# FUENTE 2: FINANCIAL MODELING PREP (FMP)
# ---------------------------------------------------------------------------
def _from_fmp(ticker: str, d: dict, fmp_key: str) -> bool:
    if not fmp_key:
        return False
    t = ticker.upper()
    try:
        # a) Perfil de empresa
        r = requests.get(
            f"https://financialmodelingprep.com/api/v3/profile/{t}?apikey={fmp_key}",
            timeout=6
        ).json()
        if r and isinstance(r, list) and r[0]:
            p = r[0]
            _fill(d, "nombre",      p.get("companyName", "N/A"))
            _fill(d, "sector",      p.get("sector",      "N/A"))
            _fill(d, "industria",   p.get("industry",    "N/A"))
            _fill(d, "descripcion", (p.get("description","") or "")[:400] + "...")
            _fill(d, "beta",        p.get("beta"))
            _fill(d, "mcap",        p.get("mktCap"))
            _fill(d, "volumen_avg", p.get("volAvg"))
            if d["precio"] == 0.0:
                _fill(d, "precio",  p.get("price", 0.0))

        # b) Ratios financieros
        r2 = requests.get(
            f"https://financialmodelingprep.com/api/v3/ratios-ttm/{t}?apikey={fmp_key}",
            timeout=6
        ).json()
        if r2 and isinstance(r2, list) and r2[0]:
            rt = r2[0]
            _fill(d, "pe",           rt.get("peRatioTTM"))
            _fill(d, "fwd_pe",       rt.get("priceEarningsToGrowthRatioTTM"))
            _fill(d, "pb",           rt.get("priceToBookRatioTTM"))
            _fill(d, "ps",           rt.get("priceToSalesRatioTTM"))
            _fill(d, "current_ratio",rt.get("currentRatioTTM"))
            _fill(d, "quick_ratio",  rt.get("quickRatioTTM"))
            _fill(d, "deuda_eq",     rt.get("debtEquityRatioTTM"))
            _fill(d, "payout_ratio", _pct(rt.get("dividendYieldTTM",0)))
            _fill(d, "div_yield",    _pct(rt.get("dividendYieldPercentageTTM",0)))
            roe = rt.get("returnOnEquityTTM")
            roa = rt.get("returnOnAssetsTTM")
            _fill(d, "roe",         _pct(roe) if _v(roe) else "N/A")
            _fill(d, "roa",         _pct(roa) if _v(roa) else "N/A")
            _fill(d, "margen_bruto",_pct(rt.get("grossProfitMarginTTM")))
            _fill(d, "margen_op",   _pct(rt.get("operatingProfitMarginTTM")))
            _fill(d, "margen_neto", _pct(rt.get("netProfitMarginTTM")))
            _fill(d, "ev_ebitda",   rt.get("enterpriseValueMultipleTTM"))
            _fill(d, "peg",         rt.get("priceEarningsToGrowthRatioTTM"))

        # c) Analyst price targets
        r3 = requests.get(
            f"https://financialmodelingprep.com/api/v3/analyst-price-targets?symbol={t}&page=0&apikey={fmp_key}",
            timeout=6
        ).json()
        if r3 and isinstance(r3, list) and len(r3) > 0:
            recents = r3[:15]
            targets = [float(x["priceTarget"]) for x in recents if _v(x.get("priceTarget"))]
            if targets:
                median_target = sorted(targets)[len(targets)//2]
                _fill(d, "target_price", median_target)
                _fill(d, "n_analistas",  len(targets))
                if _v(d.get("precio")):
                    up = ((median_target / float(d["precio"])) - 1) * 100
                    _fill(d, "upside_pct", round(up, 2))

        d["_source"].append("FMP")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# FUENTE 3: ALPHA VANTAGE (con rotación de claves)
# ---------------------------------------------------------------------------
def _from_alpha_vantage(ticker: str, d: dict, av_keys: list) -> bool:
    key = get_next_av_key(av_keys)
    if not key:
        return False
    t_av = ticker.replace("-", ".")
    try:
        r = requests.get(
            f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={t_av}&apikey={key}",
            timeout=6
        ).json()

        if "Note" in r or "Information" in r:
            mark_av_key_exhausted(key)
            return False

        increment_av_calls(key)

        if "Symbol" not in r:
            return False

        _fill(d, "nombre",       r.get("Name"))
        _fill(d, "sector",       r.get("Sector"))
        _fill(d, "industria",    r.get("Industry"))
        _fill(d, "descripcion",  (r.get("Description","") or "")[:400] + "...")
        _fill(d, "pe",           r.get("PERatio"))
        _fill(d, "fwd_pe",       r.get("ForwardPE"))
        _fill(d, "peg",          r.get("PEGRatio"))
        _fill(d, "pb",           r.get("PriceToBookRatio"))
        _fill(d, "ps",           r.get("PriceToSalesRatioTTM"))
        _fill(d, "ev_ebitda",    r.get("EVToEBITDA"))
        _fill(d, "beta",         r.get("Beta"))
        _fill(d, "mcap",         r.get("MarketCapitalization"))
        _fill(d, "ebitda",       r.get("EBITDA"))
        _fill(d, "semana52_max", r.get("52WeekHigh"))
        _fill(d, "semana52_min", r.get("52WeekLow"))
        _fill(d, "div_yield",    _pct(r.get("DividendYield", 0)))
        _fill(d, "payout_ratio", _pct(r.get("PayoutRatio", 0)))
        _fill(d, "n_analistas",  r.get("AnalystTargetPrice"))  # AV da 1 solo target
        _fill(d, "target_price", r.get("AnalystTargetPrice"))
        roe = r.get("ReturnOnEquityTTM")
        roa = r.get("ReturnOnAssetsTTM")
        _fill(d, "roe", _pct(roe) if _v(roe) else "N/A")
        _fill(d, "roa", _pct(roa) if _v(roa) else "N/A")
        _fill(d, "margen_bruto", _pct(r.get("GrossProfitTTM",0)))
        _fill(d, "margen_op",    _pct(r.get("OperatingMarginTTM",0)))
        _fill(d, "margen_neto",  _pct(r.get("ProfitMargin",0)))
        _fill(d, "revenue_growth", _pct(r.get("QuarterlyRevenueGrowthYOY",0)))
        _fill(d, "earnings_growth",_pct(r.get("QuarterlyEarningsGrowthYOY",0)))
        _fill(d, "deuda_eq",     r.get("DebtToEquityRatioTTM"))

        d["_source"].append("AlphaVantage")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# FUENTE 4: FINNHUB
# ---------------------------------------------------------------------------
def _from_finnhub(ticker: str, d: dict, finnhub_key: str) -> bool:
    if not finnhub_key:
        return False
    t = ticker.upper()
    try:
        r = requests.get(
            f"https://finnhub.io/api/v1/stock/metric?symbol={t}&metric=all&token={finnhub_key}",
            timeout=6
        ).json()
        m = r.get("metric", {})
        if not m:
            return False

        _fill(d, "beta",         m.get("beta"))
        _fill(d, "pe",           m.get("peTTM"))
        _fill(d, "fwd_pe",       m.get("peNormalizedAnnual"))
        _fill(d, "pb",           m.get("pbAnnual"))
        _fill(d, "ps",           m.get("psTTM"))
        _fill(d, "roe",          m.get("roeTTM"))
        _fill(d, "roa",          m.get("roaTTM"))
        _fill(d, "margen_bruto", m.get("grossMarginTTM"))
        _fill(d, "margen_op",    m.get("operatingMarginTTM"))
        _fill(d, "margen_neto",  m.get("netMarginTTM"))
        _fill(d, "current_ratio",m.get("currentRatioAnnual"))
        _fill(d, "quick_ratio",  m.get("quickRatioAnnual"))
        _fill(d, "semana52_max", m.get("52WeekHigh"))
        _fill(d, "semana52_min", m.get("52WeekLow"))
        _fill(d, "revenue_growth",  m.get("revenueGrowthTTMYoy"))
        _fill(d, "earnings_growth", m.get("epsGrowthTTMYoy"))
        _fill(d, "div_yield",    m.get("dividendYieldIndicatedAnnual"))
        _fill(d, "payout_ratio", m.get("payoutRatioAnnual"))
        _fill(d, "fcf",          m.get("freeCashFlowAnnual"))

        d["_source"].append("Finnhub")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: fetch_fundamental_data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamental_data(ticker: str, force_refresh: bool = False) -> dict | None:
    """
    Obtiene datos fundamentales completos de un ticker.

    Estrategia:
    1. Caché fresco → retorna inmediatamente
    2. Yahoo Finance → fuente primaria
    3. FMP          → complementa campos faltantes
    4. Alpha Vantage→ complementa (con rotación de claves)
    5. Finnhub      → complementa
    6. Caché viejo  → último recurso, agrega flag _stale=True
    """
    t_upper = ticker.upper().strip()
    s = _secrets()

    # 1. CACHÉ FRESCO
    if not force_refresh:
        cached = get_cached(t_upper)
        if cached:
            return cached

    d = _empty_schema(t_upper)

    # 2–5. FUENTES EN CASCADA
    _from_yahoo(t_upper, d)
    _from_fmp(t_upper, d, s["fmp_key"])

    # AV solo si todavía faltan campos clave
    missing_key = not _v(d.get("pe")) or not _v(d.get("roe"))
    if missing_key:
        _from_alpha_vantage(t_upper, d, s["av_keys"])

    missing_still = not _v(d.get("pb")) or not _v(d.get("margen_op"))
    if missing_still and s["finnhub_key"]:
        _from_finnhub(t_upper, d, s["finnhub_key"])

    # Guardamos en caché si obtuvimos datos reales
    if d["precio"] > 0 or _v(d.get("nombre")):
        set_cache(t_upper, d)
        return d

    # 6. CACHÉ VIEJO (stale fallback)
    stale = get_stale(t_upper)
    if stale:
        stale["_stale"] = True
        return stale

    return None


# ---------------------------------------------------------------------------
# RSI EN LOTE (Radar)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_rsi_batch(tickers: list) -> dict:
    if not tickers:
        return {}
    try:
        data = yf.download(tickers, period="1mo", interval="1d", progress=False, auto_adjust=True)["Close"]
        results = {}
        for t in tickers:
            try:
                prices = data[t].dropna() if isinstance(data, pd.DataFrame) and t in data.columns else data.dropna()
                if len(prices) < 15:
                    continue
                delta = prices.diff()
                gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
                loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
                if loss.iloc[-1] == 0:
                    results[t] = 100.0 if gain.iloc[-1] > 0 else 50.0
                    continue
                rs = gain / loss
                results[t] = round(float(100 - (100 / (1 + rs.iloc[-1]))), 2)
            except Exception:
                continue
        return results
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# DATOS EN LOTE (Análisis de Cartera)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_batch_data(tickers: list) -> dict:
    if not tickers:
        return {}
    try:
        if len(tickers) == 1:
            df = yf.download(tickers[0], period="6mo", progress=False, auto_adjust=True)
            return {tickers[0]: df} if not df.empty else {}
        raw = yf.download(tickers, period="6mo", group_by="ticker", progress=False, auto_adjust=True)
        return raw
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# DATOS DE ANALISTAS EN LOTE (para pestaña Analistas)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_analyst_batch(tickers: list, fmp_key: str) -> list:
    """
    Obtiene recomendaciones y target prices de analistas para una lista de tickers
    usando FMP (mucho más confiable que Yahoo en modo batch).
    """
    resultados = []
    if not fmp_key:
        return resultados

    for t in tickers:
        try:
            # Price targets recientes
            r = requests.get(
                f"https://financialmodelingprep.com/api/v3/analyst-price-targets?symbol={t}&page=0&apikey={fmp_key}",
                timeout=5
            ).json()

            if not r or not isinstance(r, list):
                continue

            recents = r[:20]
            targets = [float(x["priceTarget"]) for x in recents if _v(x.get("priceTarget"))]
            if not targets:
                continue

            # Tomamos el precio del primero que lo tenga
            precio_actual = next((float(x["priceWhenPosted"]) for x in recents if _v(x.get("priceWhenPosted"))), None)
            if not precio_actual:
                continue

            median_t = sorted(targets)[len(targets) // 2]
            upside   = round(((median_t / precio_actual) - 1) * 100, 2)
            if upside <= 0:
                continue

            # Recomendación agregada (grades)
            rg = requests.get(
                f"https://financialmodelingprep.com/api/v3/grade/{t}?limit=10&apikey={fmp_key}",
                timeout=4
            ).json()
            grades_str = "N/A"
            if rg and isinstance(rg, list):
                recent_grades = [g.get("newGrade","") for g in rg[:5] if g.get("newGrade")]
                if recent_grades:
                    from collections import Counter
                    grades_str = Counter(recent_grades).most_common(1)[0][0]

            resultados.append({
                "Ticker":       t,
                "Precio":       precio_actual,
                "Target Med.":  median_t,
                "Upside %":     upside,
                "# Analistas":  len(targets),
                "Consenso":     grades_str,
            })
            time.sleep(0.2)  # Respetar rate-limit de FMP
        except Exception:
            continue

    return resultados