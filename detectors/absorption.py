import time
import config
from detectors.signals import SignalType

async def detect_absorption(j, recent_trades, logger):
    recent = list(recent_trades)[-50:]
    if len(recent) < 20:
        return
    sell = sum(t.get("volume", 0) for t in recent if t.get("side") == "SELL")
    buy = sum(t.get("volume", 0) for t in recent if t.get("side") == "BUY")
    prices = [t.get("price", 0) for t in recent]
    move = max(prices) - min(prices) if len(prices) >= 2 else 0
    thr = getattr(config, 'ABSORPTION_THRESHOLD', 2000)
    if sell > thr and move < 0.02:
        j.set(SignalType.ABSORPTION, {"type": "BUYER", "sell_vol": sell}, f"S={sell:,}", "BULLISH")
        logger.warning("🔥 ABS")
    elif buy > thr and move < 0.02:
        j.set(SignalType.ABSORPTION, {"type": "SELLER", "buy_vol": buy}, f"B={buy:,}", "BEARISH")
        logger.warning("🔥 ABS")
