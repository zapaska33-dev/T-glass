#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import time


class DeltaTracker:
    def __init__(self, window_seconds: int = 60):
        self.delta = 0
        self.history = deque(maxlen=1000)
        self.window_seconds = window_seconds

    def update(self, signed_volume: int) -> int:
        """Обновление дельты"""
        self.delta += signed_volume
        self.history.append({
            'volume': signed_volume,
            'time': time.time()
        })
        return self.delta

    def get_window_delta(self, seconds: int = None) -> int:
        """Дельта за окно"""
        if seconds is None:
            seconds = self.window_seconds

        cutoff = time.time() - seconds
        window_delta = 0

        for h in self.history:
            if h['time'] >= cutoff:
                window_delta += h['volume']

        return window_delta

    def reset(self):
        """Сброс дельты"""
        self.delta = 0
        self.history.clear()