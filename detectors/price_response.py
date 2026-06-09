import time
import config
from detectors.signals import SignalType

async def detect_price_response(j, recent_trades, logger):
    recent = list(recent_trades)[-100:]
    if len(recent) < 30:
        return
    sell = sum(t.get("volume", 0) for t in recent if t.get("side") == "SELL")
    buy = sum(t.get("volume", 0) for t in recent if t.get("side") == "BUY")
    prices = [t.get("price", 0) for t in recent]
    move = prices[-1] - prices[0] if len(prices) >= 2 else 0
    thr = getattr(config, 'PRICE_RESPONSE_THRESHOLD', 1000)
    if sell > thr and move >= -0.01:
        j.set(SignalType.PRICE_RESPONSE, {"direction": "BULLISH", "sell_vol": sell}, f"S={sell:,}", "BULLISH")
        logger.warning("📊 PR")
    elif buy > thr and move <= 0.01:
        j.set(SignalType.PRICE_RESPONSE, {"direction": "BEARISH", "buy_vol": buy}, f"B={buy:,}", "BEARISH")
        logger.warning("📊 PR")
