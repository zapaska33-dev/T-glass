#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import time
import config


class TapeSpeedDetector:
    def __init__(self, window_seconds: int = 1):
        self.trades = deque(maxlen=100)
        self.window_seconds = window_seconds
        self.last_check = time.time()

    def update(self, journal, logger):
        """Обновление детектора скорости ленты"""
        now = time.time()

        # Очистка старых
        cutoff = now - self.window_seconds
        while self.trades and self.trades[0] < cutoff:
            self.trades.popleft()

        # Добавляем текущую сделку
        self.trades.append(now)

        # Проверяем скорость
        if len(self.trades) >= getattr(config, 'TAPE_SPEED_THRESHOLD', 15):
            speed = len(self.trades) / self.window_seconds
            journal.set(
                SignalType.TAPE_SPEED,
                {"speed": speed, "count": len(self.trades)},
                f"{speed:.1f} t/s",
                ""
            )
            logger.warning(f"⚡ TAPE SPEED {speed:.1f}")
            return True

        return False


from .signals import SignalType