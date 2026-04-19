# logic_external.py

def get_external_links(ticker):
    """Genera links directos a plataformas financieras para un ticker dado."""
    t = ticker.upper().strip()
    return {
        "Yahoo Finance": f"https://finance.yahoo.com/quote/{t}",
        "Finviz": f"https://finviz.com/quote.ashx?t={t}",
        "Investing": f"https://www.investing.com/search/?q={t}",
        "TradingView": f"https://www.tradingview.com/symbols/{t}/"
    }