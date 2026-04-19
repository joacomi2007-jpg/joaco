# logic_finance.py
# Nota: motor.py era un duplicado de este módulo y puede eliminarse.
# Toda la lógica financiera vive aquí.
import pandas as pd


def calcular_rsi(series: pd.Series, p: int = 14) -> float:
    """
    Calcula el RSI (Relative Strength Index) de una serie de precios.

    Returns:
        RSI entre 0 y 100. Devuelve 50.0 si no hay suficientes datos.
    """
    if len(series) < p + 1:
        return 50.0

    delta = series.diff()
    gain  = delta.where(delta > 0, 0.0).rolling(p).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(p).mean()

    last_loss = loss.iloc[-1]
    last_gain = gain.iloc[-1]

    if last_loss == 0:
        return 100.0 if last_gain > 0 else 50.0

    rs  = last_gain / last_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 2)


def evaluar_multifactor(rsi: float, precio: float, sma_50: float) -> tuple[str, str, int]:
    """
    Score de oportunidad combinando momentum (RSI) y tendencia (SMA 50).

    Puntuación:
        +3  RSI ≤ 35  (sobreventa fuerte)
        +2  Precio < SMA 50  (dip de tendencia)
        -3  RSI ≥ 65  (sobrecompra)
        -2  Precio > SMA 50 × 1.15  (extensión excesiva)

    Returns:
        (etiqueta: str, color: str, score: int)
    """
    score = 0
    import math

    # Ignoramos la SMA si no es un número válido (ej. primeros días sin historial)
    sma_valida = isinstance(sma_50, (int, float)) and not math.isnan(sma_50) and sma_50 > 0

    if rsi <= 35:
        score += 3
    elif rsi >= 65:
        score -= 3

    if sma_valida:
        if precio < sma_50:
            score += 2
        elif precio > sma_50 * 1.15:
            score -= 2

    if   score >= 3:  return "🔥 COMPRA FUERTE",  "green",     score
    elif score >= 1:  return "🟢 COMPRA",          "lightgreen",score
    elif score <= -3: return "📢 VENTA URGENTE",   "red",       score
    elif score <= -1: return "🟠 VENTA / CAUTELA", "orange",    score
    else:             return "⚖️ MANTENER",         "gray",      score


def calcular_roi_detallado(
    cant: float, costo_unitario: float, precio_actual: float
) -> tuple[float, float, float]:
    """
    Calcula el valor actual, ganancia neta y rendimiento porcentual.

    Args:
        cant:           Cantidad de acciones/CEDEARs.
        costo_unitario: Precio promedio de compra por unidad.
        precio_actual:  Precio de mercado actual por unidad.

    Returns:
        (valor_actual, ganancia_neta, rendimiento_pct)
    """
    inversion_total = cant * costo_unitario
    if inversion_total <= 0:
        return 0.0, 0.0, 0.0

    valor_actual_total = cant * precio_actual
    ganancia_neta      = valor_actual_total - inversion_total
    rendimiento_pct    = (ganancia_neta / inversion_total) * 100

    return round(valor_actual_total, 2), round(ganancia_neta, 2), round(rendimiento_pct, 2)