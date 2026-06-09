import config
from detectors.signals import SignalType

async def detect_imbalance(j, orderbook, logger):
    if orderbook.ask_size == 0:
        return
    ratio = orderbook.bid_size / orderbook.ask_size
    if ratio >= 2.0:
        j.set(SignalType.IMBALANCE, {"dominant": "BID", "ratio": ratio}, f"R={ratio:.2f}", "BULLISH")
        logger.warning(f"⚖️ IMB BID")
    elif ratio <= 0.5:
        j.set(SignalType.IMBALANCE, {"dominant": "ASK", "ratio": ratio}, f"R={ratio:.2f}", "BEARISH")
        logger.warning(f"⚖️ IMB ASK")
