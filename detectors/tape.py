import time
import config
from detectors.signals import SignalType

class TapeSpeedDetector:
    def __init__(self):
        self.cnt = 0
        self.last_sec = int(time.time())
    def update(self, journal, logger):
        self.cnt += 1
        now = int(time.time())
        if now != self.last_sec:
            thr = getattr(config, 'TAPE_SPEED_THRESHOLD', 15)
            if self.cnt >= thr:
                journal.set(SignalType.TAPE_SPEED, {"speed":self.cnt}, f"{self.cnt} t/s", "")
                logger.warning(f"⚡ TAPE {self.cnt}")
            self.cnt, self.last_sec = 0, now
