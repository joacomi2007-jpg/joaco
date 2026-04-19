# logic_sector.py
"""
Comparación de métricas con empresas del mismo sector.
"""
import streamlit as st
import requests
import os
from statistics import median

def _fmp_key() -> str:
    try:
        return st.secrets.get("FMP_KEY", "")
    except Exception:
        return os.environ.get("FMP_KEY", "")


@st.cache_data(ttl=86400, show_spinner=False)
def get_sector_peers(sector: str, industry: str, limit: int = 15) -> list:
    """
    Obtiene empresas del mismo sector/industria desde FMP.
    Retorna lista de tickers.
    """
    fmp_key = _fmp_key()
    if not fmp_key or sector in ("N/A", None, ""):
        return []
    
    try:
        # FMP tiene endpoint de screening que permite filtrar por sector
        url = (
            f"https://financialmodelingprep.com/api/v3/stock-screener"
            f"?sector={sector.replace(' ', '%20')}"
            f"&limit={limit}&apikey={fmp_key}"
        )
        r = requests.get(url, timeout=8).json()
        if r and isinstance(r, list):
            return [x["symbol"] for x in r[:limit] if x.get("symbol")]
        return []
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def compare_with_sector(ticker: str, sector: str, industry: str, pe: float, fwd_pe: float) -> dict:
    """
    Compara el P/E y Forward P/E de un ticker con la mediana de su sector.
    
    Returns:
        {
            "sector_pe_median": float,
            "sector_fwd_pe_median": float,
            "pe_vs_sector": "BARATO" | "CARO" | "EN_LINEA",
            "fwd_pe_vs_sector": "BARATO" | "CARO" | "EN_LINEA",
            "peers_count": int,
            "peers_tickers": list,
        }
    """
    fmp_key = _fmp_key()
    if not fmp_key or sector in ("N/A", None):
        return {"error": "Sector no disponible o FMP key no configurada"}
    
    # 1. Obtener peers del sector
    peers = get_sector_peers(sector, industry, limit=15)
    if not peers:
        return {"error": "No se encontraron peers en el sector"}
    
    # Filtrar el ticker mismo
    peers = [p for p in peers if p != ticker][:10]
    
    # 2. Obtener P/E y Forward P/E de cada peer
    pes     = []
    fwd_pes = []
    
    for peer in peers:
        try:
            url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{peer}?apikey={fmp_key}"
            r = requests.get(url, timeout=5).json()
            if r and isinstance(r, list) and r[0]:
                rt = r[0]
                if rt.get("peRatioTTM") not in (None, 0):
                    pes.append(float(rt["peRatioTTM"]))
                if rt.get("priceEarningsToGrowthRatioTTM") not in (None, 0):
                    fwd_pes.append(float(rt["priceEarningsToGrowthRatioTTM"]))
        except Exception:
            continue
    
    if not pes:
        return {"error": "No se pudo obtener P/E de los peers"}
    
    # 3. Calcular medianas
    sector_pe_med     = median(pes) if pes else None
    sector_fwd_pe_med = median(fwd_pes) if fwd_pes else None
    
    # 4. Comparar
    def classify(val, ref):
        if not ref or not val:
            return "SIN_DATOS"
        if val < ref * 0.85:
            return "BARATO"
        elif val > ref * 1.15:
            return "CARO"
        else:
            return "EN_LINEA"
    
    pe_status     = classify(pe, sector_pe_med) if sector_pe_med else "SIN_DATOS"
    fwd_pe_status = classify(fwd_pe, sector_fwd_pe_med) if sector_fwd_pe_med else "SIN_DATOS"
    
    return {
        "sector_pe_median":     round(sector_pe_med, 2) if sector_pe_med else "N/D",
        "sector_fwd_pe_median": round(sector_fwd_pe_med, 2) if sector_fwd_pe_med else "N/D",
        "pe_vs_sector":         pe_status,
        "fwd_pe_vs_sector":     fwd_pe_status,
        "peers_count":          len(peers),
        "peers_tickers":        peers[:5],  # Solo mostramos los primeros 5
    }