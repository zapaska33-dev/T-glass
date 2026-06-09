import time
import config
from detectors.signals import SignalType

class SpoofDetector:
    def __init__(self):
        self.active_walls = {}
    def detect(self, prev_bids, prev_asks, curr_bids, curr_asks, journal, logger):
        thr = getattr(config, 'SPOOF_SIZE_THRESHOLD', 3000)
        for price, prev_vol in prev_asks.items():
            if prev_vol >= thr and curr_asks.get(price, 0) < prev_vol * 0.3:
                journal.set(SignalType.SPOOFING, {"side":"ASK","size":prev_vol,"price":price}, f"ASK {price:.4f}", "BULLISH")
                logger.warning(f"🎭 SPF ASK {price:.4f}")
                return True
        for price, prev_vol in prev_bids.items():
            if prev_vol >= thr and curr_bids.get(price, 0) < prev_vol * 0.3:
                journal.set(SignalType.SPOOFING, {"side":"BID","size":prev_vol,"price":price}, f"BID {price:.4f}", "BEARISH")
                logger.warning(f"🎭 SPF BID {price:.4f}")
                return True
        return False
