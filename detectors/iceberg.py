import time
import config
from detectors.signals import SignalType

class IcebergDetector:
    def __init__(self):
        self.candidates = {}
    def detect(self, price, volume, side, journal, logger):
        thr = getattr(config, 'ICEBERG_MIN_VOLUME', 500)
        if volume < thr:
            return None
        key = f"{side}:{price:.4f}"
        now = time.time()
        if key not in self.candidates:
            self.candidates[key] = {"first_seen": now, "last_seen": now, "total_volume": volume, "trades": 1, "price": price, "side": side, "alerted": False}
        else:
            c = self.candidates[key]
            c["total_volume"] += volume
            c["trades"] += 1
            c["last_seen"] = now
        to_delete = [k for k, v in self.candidates.items() if now - v["last_seen"] > 20]
        for k in to_delete:
            del self.candidates[k]
        return None
