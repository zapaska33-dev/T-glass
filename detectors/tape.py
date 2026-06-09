#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import time
import config


class TapeSpeedDetector:
    """Детектор скорости ленты (tape speed)"""
    def __init__(self):
        self.trades = deque(maxlen=100)

    def update(self, journal, logger) -> bool:
        now = time.time()
        cutoff = now - 1  # за последнюю секунду
        while self.trades and self.trades[0] < cutoff:
            self.trades.popleft()
        self.trades.append(now)

        thr = getattr(config, 'TAPE_SPEED_THRESHOLD', 15)
        if len(self.trades) >= thr:
            speed = len(self.trades)
            journal.set("TAPE_SPEED", {"speed": speed}, f"{speed} trades/sec", "")
            logger.warning(f"⚡ TAPE_SPEED {speed} trades/sec")
            return True
        return False