"""Stock quote tool backed by yfinance."""

import yfinance as yf

from tools.retry import FetchError, retrying


@retrying
def _history(ticker: str):
    hist = yf.Ticker(ticker).history(period="5d")
    if hist is None or len(hist) == 0:
        raise FetchError(f"empty price history for {ticker}")
    return hist


def get_stock_quote(ticker: str) -> dict:
    """Get the latest stock quote for a ticker symbol.

    Args:
        ticker: Stock ticker symbol, for example AAPL.

    Returns:
        A dict with ticker, price, change, change_pct, currency and as_of (ISO date).
    """
    t = ticker.strip().upper()
    hist = _history(t)
    closes = list(hist["Close"])
    price = float(closes[-1])
    change = price - float(closes[-2]) if len(closes) > 1 else 0.0
    prev = price - change
    pct = (change / prev * 100) if prev else 0.0
    try:
        currency = yf.Ticker(t).fast_info.get("currency") or "USD"
    except Exception:
        currency = "USD"
    return {
        "ticker": t,
        "price": round(price, 2),
        "change": round(change, 2),
        "change_pct": round(pct, 2),
        "currency": currency,
        "as_of": hist.index[-1].date().isoformat(),
    }
