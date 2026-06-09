import config
from detectors.signals import SignalType

async def detect_wall(j, orderbook, logger):
    sz = getattr(config, 'BIG_WALL_SIZE', 5000)
    for p, v in orderbook.curr_bids.items():
        if v >= sz:
            j.set(SignalType.WALL, {"side": "BID", "price": p, "size": v}, f"BID {p:.4f}", "BULLISH")
            logger.warning(f"🧱 WALL BID")
            return
    for p, v in orderbook.curr_asks.items():
        if v >= sz:
            j.set(SignalType.WALL, {"side": "ASK", "price": p, "size": v}, f"ASK {p:.4f}", "BEARISH")
            logger.warning(f"🧱 WALL ASK")
            return
