from detectors.signals import SignalType

async def detect_liquidity_shift(j, orderbook, logger):
    if not hasattr(detect_liquidity_shift, "last_bid"):
        detect_liquidity_shift.last_bid = orderbook.bid_size
        detect_liquidity_shift.last_ask = orderbook.ask_size
        return
    bch = abs(orderbook.bid_size - detect_liquidity_shift.last_bid) / max(detect_liquidity_shift.last_bid, 1)
    ach = abs(orderbook.ask_size - detect_liquidity_shift.last_ask) / max(detect_liquidity_shift.last_ask, 1)
    detect_liquidity_shift.last_bid = orderbook.bid_size
    detect_liquidity_shift.last_ask = orderbook.ask_size
    if bch > 0.5:
        j.set(SignalType.LIQUIDITY_SHIFT, {"direction": "BID_SHIFT", "change": bch}, f"BID ch={bch * 100:.0f}%", "BULLISH")
        logger.warning(f"🌊 LIQ BID")
    elif ach > 0.5:
        j.set(SignalType.LIQUIDITY_SHIFT, {"direction": "ASK_SHIFT", "change": ach}, f"ASK ch={ach * 100:.0f}%", "BEARISH")
        logger.warning(f"🌊 LIQ ASK")
