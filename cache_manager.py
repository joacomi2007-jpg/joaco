# cache_manager.py
"""
Sistema de caché local para datos fundamentales.
- TTL: 7 días (datos se refrescan automáticamente una vez por semana).
- Fallback: si todas las APIs fallan, usa datos viejos con advertencia.
- Rotación de claves AV: detecta claves agotadas y cambia automáticamente.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

CACHE_DIR      = Path("./data_cache")
CACHE_TTL_DAYS = 7
CACHE_TTL_SEC  = CACHE_TTL_DAYS * 24 * 3600
AV_STATE_FILE  = CACHE_DIR / ".av_state.json"


# ---------------------------------------------------------------------------
# CACHÉ DE DATOS FUNDAMENTALES
# ---------------------------------------------------------------------------

def get_cached(ticker: str) -> dict | None:
    """Devuelve datos del caché si son frescos (< 7 días). None si expiró o no existe."""
    path = CACHE_DIR / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)
        age = time.time() - entry.get("ts", 0)
        return entry["data"] if age < CACHE_TTL_SEC else None
    except Exception:
        return None


def get_stale(ticker: str) -> dict | None:
    """Devuelve datos aunque estén expirados (último recurso cuando todas las APIs fallan)."""
    path = CACHE_DIR / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)
        return entry.get("data")
    except Exception:
        return None


def set_cache(ticker: str, data: dict) -> None:
    """Guarda datos en caché con timestamp actual."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{ticker.upper()}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "data": data}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_cache_info(ticker: str) -> dict:
    """
    Retorna metadata del caché de un ticker:
    {exists, fresh, age_hours, cached_at_str}
    """
    path = CACHE_DIR / f"{ticker.upper()}.json"
    if not path.exists():
        return {"exists": False, "fresh": False, "age_hours": None, "cached_at_str": "Sin caché"}
    try:
        with open(path, encoding="utf-8") as f:
            entry = json.load(f)
        ts        = entry.get("ts", 0)
        age_sec   = time.time() - ts
        age_hours = age_sec / 3600
        fresh     = age_sec < CACHE_TTL_SEC
        cached_at = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
        return {
            "exists":       True,
            "fresh":        fresh,
            "age_hours":    age_hours,
            "cached_at_str": f"{'✅' if fresh else '⚠️'} {cached_at} ({'fresco' if fresh else 'expirado'})"
        }
    except Exception:
        return {"exists": False, "fresh": False, "age_hours": None, "cached_at_str": "Error de lectura"}


def list_cached_tickers() -> list[str]:
    """Lista todos los tickers que tienen entrada en caché (frescos o no)."""
    if not CACHE_DIR.exists():
        return []
    return [p.stem for p in CACHE_DIR.glob("*.json") if not p.name.startswith(".")]


# ---------------------------------------------------------------------------
# ROTACIÓN Y ESTADO DE CLAVES ALPHA VANTAGE
# ---------------------------------------------------------------------------

def _load_av_state() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    if AV_STATE_FILE.exists():
        try:
            with open(AV_STATE_FILE, encoding="utf-8") as f:
                state = json.load(f)
            # Resetear si es un nuevo día
            if state.get("date") != today:
                return {"date": today, "exhausted": [], "call_counts": {}}
            return state
        except Exception:
            pass
    return {"date": today, "exhausted": [], "call_counts": {}}


def _save_av_state(state: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(AV_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def get_next_av_key(all_keys: list[str]) -> str | None:
    """
    Devuelve la próxima clave AV disponible (no agotada hoy).
    Retorna None si todas las claves del día se agotaron.
    """
    if not all_keys:
        return None
    state     = _load_av_state()
    exhausted = set(state.get("exhausted", []))
    available = [k for k in all_keys if k and k not in exhausted]
    return available[0] if available else None


def mark_av_key_exhausted(key: str) -> None:
    """Marca una clave AV como agotada para el día de hoy."""
    state = _load_av_state()
    if key not in state["exhausted"]:
        state["exhausted"].append(key)
    _save_av_state(state)


def increment_av_calls(key: str) -> int:
    """Incrementa el contador de llamadas de una clave. Retorna el total de hoy."""
    state  = _load_av_state()
    counts = state.setdefault("call_counts", {})
    counts[key] = counts.get(key, 0) + 1
    # AV free = 25 calls/día por clave. Marcamos como agotada al llegar a 24.
    if counts[key] >= 24:
        if key not in state["exhausted"]:
            state["exhausted"].append(key)
    _save_av_state(state)
    return counts[key]


def get_av_status(all_keys: list[str]) -> dict:
    """Retorna estado de uso de las claves AV para mostrar en UI."""
    state  = _load_av_state()
    counts = state.get("call_counts", {})
    result = {}
    for k in all_keys:
        used      = counts.get(k, 0)
        exhausted = k in state.get("exhausted", [])
        result[k[-8:]] = {   # Solo los últimos 8 chars para no exponer la clave completa
            "used":      used,
            "remaining": max(0, 24 - used),
            "exhausted": exhausted,
        }
    return result