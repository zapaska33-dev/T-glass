#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import time


class IcebergDetector:
    def __init__(self, window_seconds: int = 60):
        self.history = deque(maxlen=100)
        self.window_seconds = window_seconds

    def detect(self, volume: int, price: float, timestamp: float,
               journal, logger) -> bool:
        """Детектирование айсберга"""
        self.history.append({
            'volume': volume,
            'price': price,
            'time': timestamp
        })

        # Очистка старых записей
        cutoff = timestamp - self.window_seconds
        while self.history and self.history[0]['time'] < cutoff:
            self.history.popleft()

        # Поиск повторяющихся объемов
        if len(self.history) >= 3:
            volumes = [h['volume'] for h in self.history[-5:]]
            if len(set(volumes)) == 1 and volumes[0] >= 500:
                journal.set(
                    SignalType.ICEBERG,
                    {"volume": volumes[0], "count": len(volumes)},
                    f"V={volumes[0]} x{len(volumes)}",
                    ""
                )
                logger.warning(f"🧊 ICEBERG detected")
                return True

        return False


from .signals import SignalType