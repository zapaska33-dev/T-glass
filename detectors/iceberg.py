#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import config


class IcebergDetector:
    """Детектор айсберг-заявок"""
    def __init__(self):
        self.history = deque(maxlen=100)

    def update(self, volume: int, timestamp: float, journal, logger) -> bool:
        self.history.append({'volume': volume, 'time': timestamp})
        thr = getattr(config, 'ICEBERG_MIN_VOLUME', 500)

        # Ищем повторяющиеся объемы
        if len(self.history) >= 3:
            volumes = [h['volume'] for h in list(self.history)[-5:]]
            if len(set(volumes)) == 1 and volumes[0] >= thr:
                journal.set("ICEBERG", {"volume": volumes[0]}, f"V={volumes[0]} повторяется", "")
                logger.warning(f"🧊 ICEBERG detected: volume {volumes[0]} repeats")
                return True
        return False